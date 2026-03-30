"""
Web UI cho AI Marketing Report Pipeline.
Chạy: uvicorn app:app --reload
Truy cập: http://localhost:8000
"""
import os
import json
import base64
import subprocess
import sys
from pathlib import Path
from datetime import datetime

from fastapi import FastAPI, BackgroundTasks, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# ---------------------------------------------------------------------------
# Cấu hình đường dẫn
# ---------------------------------------------------------------------------
PROJECT_ROOT   = Path(__file__).parent
PROCESSED_DIR  = PROJECT_ROOT / "data" / "processed"
CHART_PATH     = PROCESSED_DIR / "sales_report.png"
REPORT_GLOB    = "*.md"

app = FastAPI(title="AI Marketing Report")

templates = Jinja2Templates(directory=str(PROJECT_ROOT / "templates"))

# Serve ảnh tĩnh từ data/processed
if PROCESSED_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(PROCESSED_DIR)), name="static")

# ---------------------------------------------------------------------------
# Pipeline State Management
# ---------------------------------------------------------------------------
PIPELINE_STATUS = {
    "status": "IDLE", # IDLE, RUNNING, COMPLETED, FAILED
    "start_time": None,
    "end_time": None,
    "pid": None
}
LOG_FILE = PROJECT_ROOT / "data" / "pipeline.log"


# ---------------------------------------------------------------------------
# Helper: đọc report Markdown mới nhất
# ---------------------------------------------------------------------------
def _read_latest_report() -> tuple[str, str]:
    """Trả về (filename, nội dung markdown) của report mới nhất."""
    files = sorted(PROCESSED_DIR.glob(REPORT_GLOB), key=os.path.getmtime, reverse=True)
    if not files:
        return "", ""
    f = files[0]
    return f.name, f.read_text(encoding="utf-8")


def _chart_to_base64() -> str:
    """Chuyển ảnh PNG thành base64 để nhúng thẳng vào HTML — không phụ thuộc path."""
    if not CHART_PATH.exists():
        return ""
    with open(CHART_PATH, "rb") as fh:
        return base64.b64encode(fh.read()).decode()


def _md_to_html_sections(md: str) -> list[dict]:
    """
    Parse Markdown thủ công thành list section dạng:
    [{"heading": "...", "body_html": "..."}, ...]
    Không dùng thư viện ngoài để giữ dependencies tối thiểu.
    """
    import re
    sections = []
    current_heading = "Tổng quan chiến lược"
    current_lines: list[str] = []

    def flush():
        nonlocal current_heading, current_lines
        if current_lines:
            body = "\n".join(current_lines).strip()
            # Basic MD to HTML
            body = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", body)
            body = re.sub(r"\*(.+?)\*", r"<em>\1</em>", body)
            body = re.sub(r"`(.+?)`", r"<code>\1</code>", body)
            # Table conversion
            body = _md_table_to_html(body)
            # Image conversion (data/processed/ -> /static/)
            body = re.sub(r"!\[(.*?)\]\((.*?\/)?(.*?\.png)\)", r'<img src="/static/\3" alt="\1" class="report-img">', body)
            # Paragraphs
            body = re.sub(r"\n{2,}", "</p><p>", body)
            body = f"<p>{body}</p>"
            sections.append({"heading": current_heading or "Tổng quan", "body_html": body})
            current_lines = []

    # Xử lý trường hợp Agent trả về tất cả trên 1 dòng duy nhất
    if "\n" not in md and "##" in md:
        # Tách dựa trên pattern ## 
        parts = re.split(r"(##\s+.+?)(?=##|$)", md)
        for part in parts:
            part = part.strip()
            if not part: continue
            # header_match = re.match(r"^##+\s+(.+?)$", part) # Trường hợp part chỉ là header (ít gặp)
            header_content_match = re.match(r"^##+\s+(.+?)\s+(.*)", part, re.DOTALL)
            if header_content_match:
                if current_lines: flush()
                current_heading = header_content_match.group(1).strip()
                current_lines = [header_content_match.group(2).strip()]
            else:
                current_lines.append(part)
    else:
        # Xử lý theo dòng như bình thường
        for line in md.splitlines():
            header_match = re.search(r"^(#+|##+)\s+(.+)", line.strip())
            if header_match:
                if current_lines: flush()
                current_heading = header_match.group(2).strip()
            else:
                current_lines.append(line)
    
    if current_lines:
        flush()
        
    return sections


def _md_table_to_html(text: str) -> str:
    """Chuyển bảng Markdown trong text thành bảng HTML."""
    import re
    lines = text.split("\n")
    result, i = [], 0
    while i < len(lines):
        if "|" in lines[i] and i + 1 < len(lines) and re.match(r"[\|\-\s]+", lines[i + 1]):
            headers = [c.strip() for c in lines[i].strip("|").split("|")]
            i += 2  # skip separator
            rows = []
            while i < len(lines) and "|" in lines[i]:
                rows.append([c.strip() for c in lines[i].strip("|").split("|")])
                i += 1
            th = "".join(f"<th>{h}</th>" for h in headers)
            trs = "".join(
                "<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>"
                for r in rows
            )
            result.append(f'<table><thead><tr>{th}</tr></thead><tbody>{trs}</tbody></table>')
        else:
            result.append(lines[i])
            i += 1
    return "\n".join(result)





# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    report_name, md_content = _read_latest_report()
    sections  = _md_to_html_sections(md_content) if md_content else []
    
    generated_at = datetime.now().strftime("%d/%m/%Y %H:%M")

    return templates.TemplateResponse(
        request=request, name="index.html",
        context={
            "report_name": report_name,
            "generated_at": generated_at,
            "sections": sections
        }
    )


@app.post("/run")
async def run_pipeline(background_tasks: BackgroundTasks):
    """Kick off pipeline trong background và ghi log lại."""
    if PIPELINE_STATUS["status"] == "RUNNING":
        return {"status": "error", "message": "Pipeline đang chạy, vui lòng đợi."}

    def _run():
        PIPELINE_STATUS["status"] = "RUNNING"
        PIPELINE_STATUS["start_time"] = datetime.now().isoformat()
        
        # Đảm bảo thư mục data tồn tại
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            # Xóa nội dung log cũ một cách an toàn
            if LOG_FILE.exists():
                try:
                    with open(LOG_FILE, "w", encoding="utf-8") as f:
                        f.write("")
                except PermissionError:
                    pass # Đang bị tiến trình khác giữ (ví dụ: trình duyệt đang polling)
            
            with open(LOG_FILE, "a", encoding="utf-8", buffering=1) as lf:
                process = subprocess.Popen(
                    [sys.executable, "main.py"],
                    cwd=str(PROJECT_ROOT),
                    stdout=lf,
                    stderr=lf,
                    env={**os.environ, "PYTHONUTF8": "1", "PYTHONUNBUFFERED": "1"}
                )
                PIPELINE_STATUS["pid"] = process.pid
                process.wait()
                
                if process.returncode == 0:
                    PIPELINE_STATUS["status"] = "COMPLETED"
                else:
                    PIPELINE_STATUS["status"] = "FAILED"
        except Exception as e:
            PIPELINE_STATUS["status"] = "FAILED"
            with open(LOG_FILE, "a", encoding="utf-8") as lf:
                lf.write(f"\n[SYSTEM ERROR]: {str(e)}")
        
        PIPELINE_STATUS["end_time"] = datetime.now().isoformat()

    background_tasks.add_task(_run)
    return {"status": "started", "message": "Pipeline đã khởi động."}


@app.get("/api/pipeline-status")
async def get_pipeline_status():
    return PIPELINE_STATUS


@app.get("/api/pipeline-logs")
async def get_pipeline_logs():
    try:
        # Sử dụng rb và decode để tránh lỗi lock file trên Windows
        if not LOG_FILE.exists():
            return {"logs": "Chưa có dữ liệu log."}
        with open(LOG_FILE, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        return {"logs": content}
    except PermissionError:
        return {"logs": "Đang cập nhật log (Permission Denied)..."}
    except Exception as e:
        return {"logs": f"Lỗi đọc log: {str(e)}"}


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "report_exists": PROCESSED_DIR.exists() and any(PROCESSED_DIR.glob("*.md")),
        "timestamp":     datetime.now().isoformat(),
    }


# ---------------------------------------------------------------------------
# Dashboard KPI Summary (Intelligence page)
# ---------------------------------------------------------------------------
@app.get("/api/kpi-summary")
async def get_kpi_summary(brand: str = None, region: str = None):
    db_path = PROJECT_ROOT / "data" / "raw" / "marketing_intelligence.db"
    if not db_path.exists():
        return {"error": "Database not found"}
    import sqlite3
    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        
        where_sales = []
        params_sales = []
        if brand and brand != "All" and brand != "":
            where_sales.append("brand LIKE ?")
            params_sales.append(f"%{brand}%")
        if region and region != "All" and region != "":
            where_sales.append("region LIKE ?")
            params_sales.append(f"%{region}%")
        
        where_str = " WHERE " + " AND ".join(where_sales) if where_sales else ""
        
        cur.execute(f"SELECT SUM(units_sold*unit_price) FROM sales{where_str}", params_sales)
        total_revenue = cur.fetchone()[0] or 0
        cur.execute(f"SELECT SUM(units_sold) FROM sales{where_str}", params_sales)
        total_units = cur.fetchone()[0] or 0
        
        # fallback to no filter for campaigns as it has no brand/region unless joined
        cur.execute("SELECT ROUND(AVG(roi), 2) FROM marketing_campaigns")
        avg_roi = cur.fetchone()[0] or 0
        cur.execute("SELECT ROUND(AVG(positive_score) * 100, 1) FROM social_sentiment")
        avg_sentiment = cur.fetchone()[0] or 0
        cur.execute("SELECT COUNT(*) FROM marketing_campaigns WHERE status = 'Active'")
        active_campaigns = cur.fetchone()[0] or 0
        
        cur.execute(f"SELECT model_name as product_name, SUM(units_sold*unit_price) as revenue FROM sales{where_str} GROUP BY model_name ORDER BY revenue DESC LIMIT 1", params_sales)
        top_product = cur.fetchone()
        
        cur.execute("SELECT channel FROM marketing_campaigns ORDER BY roi DESC LIMIT 1")
        tc = cur.fetchone()
        top_channel = tc[0] if tc else "N/A"
        
        cur.execute("SELECT top_complaint FROM social_sentiment GROUP BY top_complaint ORDER BY COUNT(*) DESC LIMIT 1")
        tcomp = cur.fetchone()
        top_complaint = tcomp[0] if tcomp else "N/A"
    return {
        "total_revenue": total_revenue,
        "total_units": total_units,
        "avg_roi": avg_roi,
        "avg_sentiment": avg_sentiment,
        "active_campaigns": active_campaigns,
        "top_product": top_product[0] if top_product else "N/A",
        "top_product_revenue": top_product[1] if top_product else 0,
        "top_channel": top_channel,
        "top_complaint": top_complaint
    }


# ---------------------------------------------------------------------------
# Analytics (Chart Data)
# ---------------------------------------------------------------------------
@app.get("/api/dashboard-data")
async def get_dashboard_data(brand: str = None, region: str = None):
    db_path = PROJECT_ROOT / "data" / "raw" / "marketing_intelligence.db"
    if not db_path.exists():
        return {"error": "Database not found"}
        
    import sqlite3
    data = {}
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        where_sales = []
        params_sales = []
        if brand and brand != "All" and brand != "":
            where_sales.append("brand LIKE ?")
            params_sales.append(f"%{brand}%")
        if region and region != "All" and region != "":
            where_sales.append("region LIKE ?")
            params_sales.append(f"%{region}%")
            
        where_str = " WHERE " + " AND ".join(where_sales) if where_sales else ""
        
        # ── MODULE 1: Performance Ranking ──
        cur.execute(f"SELECT model_name as product_name, SUM(units_sold*unit_price) as revenue FROM sales{where_str} GROUP BY model_name ORDER BY revenue DESC LIMIT 5", params_sales)
        data['top_revenue'] = [dict(r) for r in cur.fetchall()]
        cur.execute(f"SELECT model_name as product_name, SUM(units_sold) as units_sold FROM sales{where_str} GROUP BY model_name ORDER BY units_sold DESC LIMIT 5", params_sales)
        data['top_sales'] = [dict(r) for r in cur.fetchall()]
        
        cur.execute(f"SELECT model_name as product_name, SUM(units_sold*unit_price) as revenue FROM sales{where_str} GROUP BY model_name ORDER BY revenue ASC LIMIT 5", params_sales)
        data['bottom_revenue'] = [dict(r) for r in cur.fetchall()]
        cur.execute(f"SELECT model_name as product_name, SUM(units_sold) as units_sold FROM sales{where_str} GROUP BY model_name ORDER BY units_sold ASC LIMIT 5", params_sales)
        data['bottom_sales'] = [dict(r) for r in cur.fetchall()]
        
        # ── MODULE 2: Payment Dynamics ──
        cur.execute(f"SELECT payment_method, COUNT(*) as count FROM sales{where_str} GROUP BY payment_method ORDER BY count DESC", params_sales)
        data['payment_donut'] = [dict(r) for r in cur.fetchall()]
        cur.execute(f"SELECT customer_age_group, payment_method, COUNT(*) as count FROM sales{where_str} GROUP BY customer_age_group, payment_method", params_sales)
        data['payment_age'] = [dict(r) for r in cur.fetchall()]
        
        # ── MODULE 3: Customer Profiles ──
        cur.execute(f"SELECT customer_age_group, price_bin, COUNT(*) as count FROM sales{where_str} GROUP BY customer_age_group, price_bin", params_sales)
        data['price_age_heatmap'] = [dict(r) for r in cur.fetchall()]
        
        # ── MODULE 4: Marketing Efficiency ──
        cur.execute("""
            SELECT channel, 
                   ROUND(AVG(budget * 1.0 / NULLIF(conversions, 0)), 0) as avg_cpa,
                   ROUND(AVG(roi), 2) as avg_roi,
                   ROUND(AVG(conversions * 100.0 / NULLIF(reach, 0)), 2) as avg_conv_rate
            FROM marketing_campaigns 
            GROUP BY channel
        """)
        data['marketing_efficiency'] = [dict(r) for r in cur.fetchall()]
        
    return data


# ---------------------------------------------------------------------------
# Reports Management
# ---------------------------------------------------------------------------
@app.get("/api/reports")
async def list_reports():
    """Liệt kê tất cả report .md trong data/processed."""
    if not PROCESSED_DIR.exists():
        return {"reports": []}
    files = sorted(PROCESSED_DIR.glob("*.md"), key=os.path.getmtime, reverse=True)
    reports = []
    for f in files:
        stat = f.stat()
        reports.append({
            "filename": f.name,
            "size_kb": round(stat.st_size / 1024, 1),
            "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%d/%m/%Y %H:%M"),
        })
    return {"reports": reports}


@app.get("/api/report/{filename}")
async def read_report(filename: str):
    """Đọc nội dung một report cụ thể."""
    filepath = PROCESSED_DIR / filename
    if not filepath.exists() or not filepath.suffix == ".md":
        return {"error": "File not found"}
    content = filepath.read_text(encoding="utf-8")
    sections = _md_to_html_sections(content)
    return {"filename": filename, "content": content, "sections": sections}


# ---------------------------------------------------------------------------
# Model Infrastructure Info
# ---------------------------------------------------------------------------
@app.get("/api/model-info")
async def get_model_info():
    """Trả về thông tin về LLM infrastructure."""
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env")
    
    nim_key = os.getenv("NVIDIA_NIM_API_KEY", "")
    or_key = os.getenv("OPENROUTER_API_KEY", "")
    
    return {
        "primary_model": {
            "name": "Llama 3.3 70B Instruct",
            "provider": "NVIDIA NIM",
            "model_id": "nvidia_nim/meta/llama-3.3-70b-instruct",
            "parameters": "70B",
            "temperature": 0.2,
            "context_window": "128K tokens",
            "api_connected": bool(nim_key),
        },
        "orchestrator": {
            "name": "CrewAI",
            "version": "1.11.0",
            "agents": [
                {"role": "Trưởng phòng Kinh doanh & Phân tích Thị trường", "tools": ["search_internet", "query_marketing_db"]},
                {"role": "Quản lý Chiến dịch Marketing & Sự kiện", "tools": ["query_marketing_db", "read_marketing_content"]},
                {"role": "Giám đốc Vận hành (COO) Chuỗi Bán lẻ", "tools": ["query_marketing_db", "save_report", "create_sales_chart"]},
            ]
        },
        "tools": [
            {"name": "search_internet", "type": "Web Scraper", "desc": "Tìm kiếm thông tin thị trường"},
            {"name": "query_marketing_db", "type": "SQL Query", "desc": "Truy vấn SQLite database"},
            {"name": "read_marketing_content", "type": "File Reader", "desc": "Đọc nội dung marketing nội bộ"},
            {"name": "save_report", "type": "File Writer", "desc": "Lưu báo cáo Markdown"},
            {"name": "create_sales_chart", "type": "Visualization", "desc": "Tạo biểu đồ matplotlib"},
        ],
        "backup_provider": {
            "name": "OpenRouter",
            "api_connected": bool(or_key),
        }
    }