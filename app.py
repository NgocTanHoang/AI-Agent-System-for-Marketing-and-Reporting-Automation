"""
Web UI cho AI Marketing Report Pipeline - Production Ready Version.
"""
import os
import re
import json
import base64
import subprocess
import sys
import sqlite3
import logging
from pathlib import Path
from datetime import datetime

from fastapi import FastAPI, BackgroundTasks, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

from src.config import setup_logging, DATABASE_PATH, PROCESSED_DATA_DIR, PROJECT_ROOT

# Initialize logger
logger = setup_logging("fastapi_app")

app = FastAPI(title="AI Marketing Intelligence Dashboard")

# --- CORS CONFIGURATION ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict to specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

templates = Jinja2Templates(directory=str(PROJECT_ROOT / "templates"))

# Serve static files
if PROCESSED_DATA_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(PROCESSED_DATA_DIR)), name="static")

# Pipeline State
PIPELINE_STATUS = {
    "status": "IDLE",
    "start_time": None,
    "end_time": None,
    "pid": None
}
LOG_FILE = PROJECT_ROOT / "data" / "pipeline.log"

# --- HELPERS ---

def _read_latest_report() -> tuple[str, str]:
    files = sorted(PROCESSED_DATA_DIR.glob("*.md"), key=os.path.getmtime, reverse=True)
    if not files: return "", ""
    return files[0].name, files[0].read_text(encoding="utf-8")

def _md_to_html(md_text: str) -> str:
    try:
        import markdown
        return markdown.markdown(md_text, extensions=["tables", "fenced_code", "nl2br"])
    except ImportError:
        return md_text.replace("\n", "<br>")

# --- ROUTES ---

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    report_name, md_content = _read_latest_report()
    # Simple split for sections if no markdown lib
    sections = [{"heading": "Report", "body_html": _md_to_html(md_content)}] if md_content else []
    return templates.TemplateResponse(
        "index.html", 
        {"request": request, "report_name": report_name, "sections": sections, "generated_at": datetime.now().strftime("%H:%M %d/%m/%Y")}
    )

@app.post("/run")
async def run_pipeline(background_tasks: BackgroundTasks):
    if PIPELINE_STATUS["status"] == "RUNNING":
        raise HTTPException(status_code=400, detail="Pipeline is already running.")

    def _execute():
        PIPELINE_STATUS["status"] = "RUNNING"
        PIPELINE_STATUS["start_time"] = datetime.now().isoformat()
        try:
            with open(LOG_FILE, "w", encoding="utf-8") as f: f.write("") # Clear log
            process = subprocess.Popen(
                [sys.executable, "main.py"],
                cwd=str(PROJECT_ROOT),
                stdout=open(LOG_FILE, "a"),
                stderr=open(LOG_FILE, "a"),
                env={**os.environ, "PYTHONUTF8": "1"}
            )
            PIPELINE_STATUS["pid"] = process.pid
            process.wait()
            PIPELINE_STATUS["status"] = "COMPLETED" if process.returncode == 0 else "FAILED"
        except Exception as e:
            logger.error(f"Pipeline Execution Error: {e}")
            PIPELINE_STATUS["status"] = "FAILED"
        PIPELINE_STATUS["end_time"] = datetime.now().isoformat()

    background_tasks.add_task(_execute)
    return {"status": "started"}

@app.get("/api/pipeline-status")
async def get_status():
    return PIPELINE_STATUS

@app.get("/api/pipeline-logs")
async def get_logs():
    if not LOG_FILE.exists(): return {"logs": ""}
    try:
        return {"logs": LOG_FILE.read_text(encoding="utf-8", errors="ignore")}
    except Exception:
        return {"logs": "Bận..."}

@app.get("/api/kpi-summary")
async def get_kpi_summary(brand: str = None, region: str = None):
    if not DATABASE_PATH.exists():
        return JSONResponse(status_code=500, content={"error": "Database missing"})
    
    brand_p = f"%{brand}%" if brand and brand != "All" else "%"
    region_p = f"%{region}%" if region and region != "All" else "%"

    try:
        with sqlite3.connect(str(DATABASE_PATH)) as conn:
            cur = conn.cursor()
            
            # Revenue & Units
            cur.execute("SELECT SUM(units_sold*unit_price), SUM(units_sold) FROM sales WHERE brand LIKE ? AND region LIKE ?", (brand_p, region_p))
            res = cur.fetchone()
            rev, units = res if res else (0, 0)

            # Performance
            cur.execute("SELECT ROUND(AVG(roi), 2) FROM marketing_campaigns")
            roi = cur.fetchone()[0] or 0
            
            cur.execute("SELECT ROUND(AVG(positive_score)*100, 1) FROM social_sentiment")
            sent = cur.fetchone()[0] or 0

            # Top product
            cur.execute("SELECT model_name FROM sales WHERE brand LIKE ? AND region LIKE ? GROUP BY model_name ORDER BY SUM(units_sold*unit_price) DESC LIMIT 1", (brand_p, region_p))
            tp = cur.fetchone()
            top_p = tp[0] if tp else "N/A"

            return {
                "total_revenue": rev or 0,
                "total_units": units or 0,
                "avg_roi": roi,
                "avg_sentiment": sent,
                "top_product": top_p
            }
    except Exception as e:
        logger.error(f"KPI API Error: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/api/dashboard-data")
async def get_dashboard_data(brand: str = None, region: str = None):
    if not DATABASE_PATH.exists(): return {"error": "DB missing"}
    
    brand_p = f"%{brand}%" if brand and brand != "All" else "%"
    region_p = f"%{region}%" if region and region != "All" else "%"
    
    try:
        with sqlite3.connect(str(DATABASE_PATH)) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            
            cur.execute("SELECT model_name as product_name, SUM(units_sold*unit_price) as revenue FROM sales WHERE brand LIKE ? AND region LIKE ? GROUP BY model_name ORDER BY revenue DESC LIMIT 5", (brand_p, region_p))
            top_rev = [dict(r) for r in cur.fetchall()]
            
            cur.execute("SELECT channel, ROUND(AVG(roi), 2) as avg_roi FROM marketing_campaigns GROUP BY channel")
            mkt = [dict(r) for r in cur.fetchall()]
            
            return {"top_revenue": top_rev, "marketing_efficiency": mkt}
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/reports")
async def list_reports():
    files = sorted(PROCESSED_DATA_DIR.glob("*.md"), key=os.path.getmtime, reverse=True)
    return {"reports": [{"filename": f.name, "modified": datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d %H:%M")} for f in files]}

@app.get("/api/report/{filename}")
async def get_report(filename: str):
    path = PROCESSED_DATA_DIR / filename
    if not path.exists(): raise HTTPException(status_code=404)
    content = path.read_text(encoding="utf-8")
    return {"content": content, "html": _md_to_html(content)}

# Handle Legacy or extra endpoints
@app.get("/api/social-posts")
async def social_posts():
    _, md = _read_latest_report()
    # Mock extract for demo consistency
    return {"posts": [{"label": "Viral", "hook": "Check this!", "cta": "Buy now", "hashtags": "#AI"}]}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)