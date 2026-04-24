import os
import re
import time
import sqlite3
import logging
import pandas as pd
import matplotlib.pyplot as plt
from typing import List, Optional, Any
from ddgs import DDGS
from dotenv import load_dotenv
from crewai.tools import BaseTool, tool
from pydantic import Field, PrivateAttr

load_dotenv()

# --- 1. CONFIG & LOGGING ---
logger = logging.getLogger("marketing_tools")

# --- 2. ERROR RESILIENCE: EXPONENTIAL BACKOFF ---

def retry_with_backoff(max_retries: int = 3, initial_delay: float = 1.0, backoff_factor: float = 2.0):
    """
    Decorator implementation of Exponential Backoff for API calls.
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            delay = initial_delay
            last_exception = None
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt == max_retries:
                        break
                    
                    err_msg = str(e)
                    is_retryable = any(k in err_msg for k in [
                        "Timeout", "504", "502", "503", "429", "RateLimit", "Connection"
                    ])
                    
                    if not is_retryable:
                        raise e
                        
                    logger.warning(f"Tool {func.__name__} failed (Attempt {attempt+1}/{max_retries+1}). Retrying in {delay}s...")
                    time.sleep(delay)
                    delay *= backoff_factor
            raise last_exception
        return wrapper
    return decorator

# --- 3. LANGUAGE SANITIZATION ---

def sanitize_vietnamese_text(text: str, db_path: Optional[str] = None) -> str:
    """
    1. Removes CJK characters (Chinese, Japanese, Korean).
    2. Category Hallucination Revert: Replaces generic categories with top model_name from DB.
    3. Trims whitespace.
    """
    if not text: return ""

    # a) CJK Filter (Chinese, Japanese, Korean blocks)
    cjk_pattern = re.compile(f'[\u4e00-\u9fff\u3040-\u30ff\uac00-\ud7af]')
    text = cjk_pattern.sub('', text)

    # b) Category Hallucination Revert (Anchor to SQL Ground Truth)
    # If LLM says "Smartphone" or "Electronics", we revert to the actual top seller in the DB.
    hallucination_terms = ["Điện tử", "Electronics", "Smartphone", "Điện thoại", "Thiết bị di động"]
    if any(term in text for term in hallucination_terms):
        try:
            if not db_path:
                from src.config import DATABASE_PATH
                db_path = str(DATABASE_PATH)
            
            with sqlite3.connect(db_path) as conn:
                cur = conn.cursor()
                cur.execute("SELECT model_name FROM sales GROUP BY model_name ORDER BY SUM(units_sold) DESC LIMIT 1")
                top_model = cur.fetchone()
                if top_model:
                    for term in hallucination_terms:
                        text = text.replace(term, top_model[0])
        except Exception as e:
            logger.error(f"Sanitizer Revert failed: {e}")

    return text.strip()

# --- 4. ENTERPRISE DATA TOOLS ---

class EnterpriseDataTools:
    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            from src.config import DATABASE_PATH
            self.db_path = str(DATABASE_PATH)
        else:
            self.db_path = db_path

    def _validate_query(self, query: str) -> str:
        """
        Principal Engineer's Guardrail:
        1. Prevents SQL Injection by whitelisting SELECT.
        2. Enforces LIMIT to prevent memory overflow or infinite reading.
        3. Simple blacklist for destructive commands.
        """
        q = query.strip().upper()
        
        # Guard 1: Read-only check
        if not q.startswith("SELECT"):
            raise ValueError("Chỉ chấp nhận lệnh SELECT để đảm bảo an toàn dữ liệu.")
        
        # Guard 2: Destructive keyword blacklist
        destructive = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "TRUNCATE", "EXEC", "CREATE"]
        if any(re.search(rf"\b{word}\b", q) for word in destructive):
            raise ValueError(f"Phát hiện từ khóa bị cấm: {destructive}")
        
        # Guard 3: Multiple statements check
        if ";" in query:
             # Allow if it's the last char, but block if multiple
             if query.rstrip().count(";") > 1 or not query.rstrip().endswith(";"):
                 raise ValueError("Chỉ chấp nhận một câu lệnh SQL duy nhất.")

        # Guard 4: Enforce LIMIT
        if "LIMIT" not in q:
            query = query.rstrip().rstrip(";") + " LIMIT 50"
        
        return query

    def query_marketing_db(self, query: str, output_format: str = "markdown") -> str:
        """Truy vấn SQLite Marketing Intelligence với lớp bảo mật Validated Execution."""
        try:
            validated_query = self._validate_query(query)
            
            with sqlite3.connect(self.db_path) as conn:
                # database-level read-only
                conn.execute("PRAGMA query_only = ON")
                
                df = pd.read_sql_query(validated_query, conn)
                
                if df.empty:
                    return "Không tìm thấy kết quả nào trong Database."
                
                if output_format == "markdown":
                    return df.to_markdown(index=False)
                return df.to_json(orient="records")
                
        except Exception as e:
            # Error guidance for the Agent
            err_msg = str(e)
            if "no such column: model" in err_msg.lower():
                return "Lỗi: Không có cột 'model'. Gợi ý: Hãy dùng 'model_name'."
            if "no such column: price" in err_msg.lower():
                return "Lỗi: Không có cột 'price'. Gợi ý: Dùng 'unit_price' trong bảng sales hoặc 'current_price' trong competitor_products."
            return f"SQL Error: {err_msg}"

# --- 5. STANDALONE TOOLS ---

@tool("search_internet")
@retry_with_backoff(max_retries=3)
def search_internet(query: str) -> str:
    """Quét internet để lấy tin tức mới nhất về xu hướng công nghệ hoặc đối thủ."""
    try:
        ddgs_client = DDGS()
        results = list(ddgs_client.text(query, max_results=5))
        if not results: return f"Không tìm thấy kết quả cho: {query}"
        
        formatted = []
        for r in results:
            formatted.append(f"Tiêu đề: {r['title']}\nURL: {r['href']}\nBody: {r['body']}\n")
        return "\n---\n".join(formatted)
    except Exception as e:
        logger.error(f"Search failed: {e}")
        return f"Lỗi tìm kiếm (API Timeout): {e}"

@tool("read_marketing_content")
def read_marketing_content(file_name: str) -> str:
    """Đọc tài liệu marketing nội bộ từ data/raw/marketing_content/."""
    from src.config import RAW_DATA_DIR
    content_dir = RAW_DATA_DIR / "marketing_content"
    
    # Path traversal protection
    safe_name = os.path.basename(file_name)
    file_path = content_dir / safe_name
    
    if not file_path.exists():
        # List available files to help the Agent
        available = [f.name for f in content_dir.glob("*.txt")]
        return f"File '{safe_name}' không tồn tại. File khả dụng: {available}"
    
    try:
        return file_path.read_text(encoding="utf-8")
    except Exception as e:
        return f"Lỗi đọc nội dung: {e}"

@tool("save_report")
def save_report(content: str, filename: str) -> str:
    """Lưu báo cáo chiến lược xuống định dạng Markdown (.md) sau khi đã làm sạch ngôn ngữ."""
    from src.config import PROCESSED_DATA_DIR
    
    sanitized_content = sanitize_vietnamese_text(content)
    
    safe_name = os.path.basename(filename)
    if not safe_name.endswith(".md"): safe_name += ".md"
    
    full_path = PROCESSED_DATA_DIR / safe_name
    try:
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(sanitized_content)
        return f"Báo cáo đã được lưu an toàn tại: {full_path.name}"
    except Exception as e:
        return f"Lỗi lưu file: {e}"

@tool("create_sales_chart")
def create_sales_chart(data_json: str, title: str, chart_type: str = "bar") -> str:
    """Tạo biểu đồ PNG từ dữ liệu JSON (keys: label, value). Trả về đường dẫn file."""
    from src.config import PROCESSED_DATA_DIR
    import json
    
    try:
        data = json.loads(data_json)
        df = pd.DataFrame(data)
        
        if df.empty or len(df.columns) < 2:
            return "Lỗi: Dữ liệu JSON không hợp lệ để tạo biểu đồ."
        
        plt.figure(figsize=(10, 6))
        # Assuming first col is label, second is numerical
        cols = df.columns
        plt.bar(df[cols[0]], df[cols[1]], color='skyblue')
        plt.title(title)
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        filename = f"chart_{int(time.time())}.png"
        save_path = PROCESSED_DATA_DIR / filename
        plt.savefig(save_path)
        plt.close()
        
        return f"Biểu đồ đã được tạo: {filename}"
    except Exception as e:
        return f"Lỗi tạo biểu đồ: {e}"

# --- 6. CLASSES AS TOOLS (CrewAI Style) ---

class SignalUpdateTool(BaseTool):
    name: str = "signal_update"
    description: str = "Ghi nhận bài học chiến lược (learning signals) vào database để Agent chu kỳ sau tham khảo."
    
    def _run(self, insight_type: str, learning_content: str) -> str:
        """
        Lưu ý: insight_type nên thuộc: 'low_performer', 'budget_realloc', 'trend_alert'.
        """
        from src.config import DATABASE_PATH
        try:
            with sqlite3.connect(str(DATABASE_PATH)) as conn:
                cur = conn.cursor()
                cur.execute(
                    "INSERT INTO learning_signals (insight_type, learning_content) VALUES (?, ?)",
                    (insight_type, sanitize_vietnamese_text(learning_content))
                )
                conn.commit()
            return f"✅ Đã ghi nhận signal [{insight_type}] thành công."
        except Exception as e:
            return f"Lỗi ghi signal: {e}"