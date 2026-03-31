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
    allow_origins=["*"],
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
    files = sorted(list(PROCESSED_DATA_DIR.glob("*.md")), key=os.path.getmtime, reverse=True)
    if not files: return "", ""
    return files[0].name, files[0].read_text(encoding="utf-8")

def _md_to_html(md_text: str) -> str:
    try:
        import markdown
        return markdown.markdown(md_text, extensions=["tables", "fenced_code", "nl2br"])
    except ImportError:
        return md_text.replace("\n", "<br>")

def _get_sections(md_content: str) -> list:
    """Simple markdown splitter into sections by ##."""
    if not md_content: return []
    sections = []
    blocks = re.split(r'^##\s+', md_content, flags=re.MULTILINE)
    
    # Handle the first block if it doesn't start with ##
    first = blocks[0].strip()
    if first and not md_content.startswith("##"):
        sections.append({"heading": "Tổng quan", "body_html": _md_to_html(first)})
        blocks = blocks[1:]
    
    for block in blocks:
        if not block.strip(): continue
        lines = block.split('\n', 1)
        heading = lines[0].strip()
        body = lines[1].strip() if len(lines) > 1 else ""
        sections.append({"heading": heading, "body_html": _md_to_html(body)})
    return sections

# --- ROUTES ---

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    report_name, md_content = _read_latest_report()
    sections = _get_sections(md_content)
    return templates.TemplateResponse(
        "index.html", 
        {"request": request, "report_name": report_name, "sections": sections, "generated_at": datetime.now().strftime("%H:%M %d/%m/%Y")}
    )

@app.post("/run")
async def run_pipeline(background_tasks: BackgroundTasks):
    if PIPELINE_STATUS["status"] == "RUNNING":
        return {"status": "error", "message": "Pipeline is already running."}

    def _execute():
        PIPELINE_STATUS["status"] = "RUNNING"
        PIPELINE_STATUS["start_time"] = datetime.now().isoformat()
        try:
            LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(LOG_FILE, "w", encoding="utf-8") as f: f.write("") 
            
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
            logger.error(f"Pipeline Error: {e}")
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
    if not DATABASE_PATH.exists(): return {"error": "DB missing"}
    
    brand_p = f"%{brand}%" if brand and brand != "All" else "%"
    region_p = f"%{region}%" if region and region != "All" else "%"

    try:
        with sqlite3.connect(str(DATABASE_PATH)) as conn:
            cur = conn.cursor()
            
            # Revenue & Units
            cur.execute("SELECT SUM(units_sold*unit_price), SUM(units_sold) FROM sales WHERE brand LIKE ? AND region LIKE ?", (brand_p, region_p))
            res = cur.fetchone()
            rev, units = res if res else (0, 0)

            # Marketing Metrics
            cur.execute("SELECT ROUND(AVG(roi), 2), channel FROM marketing_campaigns GROUP BY channel ORDER BY AVG(roi) DESC LIMIT 1")
            res_m = cur.fetchone()
            roi, top_channel = res_m if res_m else (0, "N/A")
            
            # Sentiment
            cur.execute("SELECT ROUND(AVG(positive_score)*100, 1), top_complaint FROM social_sentiment GROUP BY top_complaint ORDER BY COUNT(*) DESC LIMIT 1")
            res_s = cur.fetchone()
            sent, top_complaint = res_s if res_s else (0, "N/A")

            return {
                "total_revenue": rev or 0,
                "total_units": units or 0,
                "avg_roi": roi or 0,
                "avg_sentiment": sent or 0,
                "top_channel": top_channel,
                "top_complaint": top_complaint
            }
    except Exception as e:
        logger.error(f"KPI API Error: {e}")
        return {"error": str(e)}

@app.get("/api/dashboard-data")
async def get_dashboard_data(brand: str = None, region: str = None):
    if not DATABASE_PATH.exists(): return {"error": "DB missing"}
    
    brand_p = f"%{brand}%" if brand and brand != "All" else "%"
    region_p = f"%{region}%" if region and region != "All" else "%"
    
    data = {}
    try:
        with sqlite3.connect(str(DATABASE_PATH)) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            
            # ── MODULE 1: Performance Ranking ──
            cur.execute("SELECT model_name as product_name, SUM(units_sold*unit_price) as revenue FROM sales WHERE brand LIKE ? AND region LIKE ? GROUP BY model_name ORDER BY revenue DESC LIMIT 5", (brand_p, region_p))
            data['top_revenue'] = [dict(r) for r in cur.fetchall()]
            
            cur.execute("SELECT model_name as product_name, SUM(units_sold) as units_sold FROM sales WHERE brand LIKE ? AND region LIKE ? GROUP BY model_name ORDER BY units_sold DESC LIMIT 5", (brand_p, region_p))
            data['top_sales'] = [dict(r) for r in cur.fetchall()]
            
            cur.execute("SELECT model_name as product_name, SUM(units_sold*unit_price) as revenue FROM sales WHERE brand LIKE ? AND region LIKE ? GROUP BY model_name ORDER BY revenue ASC LIMIT 5", (brand_p, region_p))
            data['bottom_revenue'] = [dict(r) for r in cur.fetchall()]
            
            cur.execute("SELECT model_name as product_name, SUM(units_sold) as units_sold FROM sales WHERE brand LIKE ? AND region LIKE ? GROUP BY model_name ORDER BY units_sold ASC LIMIT 5", (brand_p, region_p))
            data['bottom_sales'] = [dict(r) for r in cur.fetchall()]
            
            # ── MODULE 2: Payment Dynamics ──
            cur.execute("SELECT payment_method, COUNT(*) as count FROM sales WHERE brand LIKE ? AND region LIKE ? GROUP BY payment_method ORDER BY count DESC", (brand_p, region_p))
            data['payment_donut'] = [dict(r) for r in cur.fetchall()]
            
            cur.execute("SELECT customer_age_group, payment_method, COUNT(*) as count FROM sales WHERE brand LIKE ? AND region LIKE ? GROUP BY customer_age_group, payment_method", (brand_p, region_p))
            data['payment_age'] = [dict(r) for r in cur.fetchall()]
            
            # ── MODULE 3: Customer Profiles ──
            cur.execute("SELECT customer_age_group, price_bin, COUNT(*) as count FROM sales WHERE brand LIKE ? AND region LIKE ? GROUP BY customer_age_group, price_bin", (brand_p, region_p))
            data['price_age_heatmap'] = [dict(r) for r in cur.fetchall()]
            
            # ── MODULE 4: Marketing Efficiency ──
            cur.execute("SELECT channel, ROUND(AVG(budget/NULLIF(conversions,0)), 0) as avg_cpa, ROUND(AVG(roi), 2) as avg_roi FROM marketing_campaigns GROUP BY channel")
            data['marketing_efficiency'] = [dict(r) for r in cur.fetchall()]
            
    except Exception as e:
        logger.error(f"Dashboard Data Error: {e}")
        return {"error": str(e)}
    
    return data

@app.get("/api/reports")
async def list_reports():
    files = sorted(list(PROCESSED_DATA_DIR.glob("*.md")), key=os.path.getmtime, reverse=True)
    return {"reports": [{"filename": f.name, "size_kb": round(f.stat().st_size/1024,1), "modified": datetime.fromtimestamp(f.stat().st_mtime).strftime("%d/%m/%Y %H:%M")} for f in files]}

@app.get("/api/report/{filename}")
async def get_report(filename: str):
    path = PROCESSED_DATA_DIR / filename
    if not path.exists(): raise HTTPException(status_code=404)
    content = path.read_text(encoding="utf-8")
    sections = _get_sections(content)
    return {"filename": filename, "content": content, "sections": sections}

@app.get("/api/model-info")
async def get_model_info():
    return {
        "primary_model": {
            "name": "Llama 3.3 70B", "provider": "NVIDIA NIM", "model_id": "meta/llama-3.3-70b-instruct",
            "parameters": "70B", "temperature": 0.3, "context_window": "128K", "api_connected": True
        },
        "orchestrator": {
            "name": "CrewAI", "version": "0.1",
            "agents": [
                {"role": "Intelligence Lead", "tools": ["search_internet", "query_marketing_db"]},
                {"role": "Brand Strategist", "tools": ["read_marketing_content"]},
                {"role": "Chief Strategy Officer (CSO)", "tools": ["query_marketing_db", "create_sales_chart"]}
            ]
        },
        "tools": [
            {"name": "search_internet", "type": "Web", "desc": "Tìm kiếm xu hướng"},
            {"name": "query_marketing_db", "type": "SQL", "desc": "Truy xuất dữ liệu"},
            {"name": "create_sales_chart", "type": "Chart", "desc": "Vẽ biểu đồ"}
        ],
        "backup_provider": {"name": "OpenRouter", "api_connected": True}
    }

@app.get("/api/social-posts")
async def social_posts():
    return {"posts": []} # Fallback

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)