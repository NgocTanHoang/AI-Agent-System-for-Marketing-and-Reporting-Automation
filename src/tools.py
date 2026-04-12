import os
import json
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import io
import time
from datetime import datetime
from ddgs import DDGS
from crewai.tools import BaseTool
from pydantic import Field
from src.config import setup_logging, DATABASE_PATH, PROCESSED_DATA_DIR, RAW_DATA_DIR, HTTP_TIMEOUT, MAX_RETRIES

# Initialize logger
logger = setup_logging("enterprise_tools")

# --- 1. KHỞI TẠO DECORATOR ---
try:
    from crewai.tools import tool
except ImportError:
    try:
        from crewai import tool
    except ImportError:
        logger.error("Không thể import CrewAI tool decorator. Đảm bảo 'crewai[tools]' đã được cài đặt.")
        raise ImportError("Không thể import CrewAI tool decorator.")

# --- 2. CÁC HÀM STANDALONE ---

def search_internet(query: str):
    """
    Quét internet để lấy tin tức mới nhất về xu hướng công nghệ hoặc đối thủ.
    Sử dụng DuckDuckGo với cơ chế retry đơn giản.
    """
    logger.info(f"Đang tìm kiếm xu hướng: {query}")
    
    for attempt in range(MAX_RETRIES):
        try:
            ddgs_client = DDGS(timeout=HTTP_TIMEOUT)
            results = list(ddgs_client.text(query, max_results=5))
            if results:
                logger.info(f"Tìm thấy {len(results)} kết quả.")
                return results
            logger.warning(f"Không tìm thấy kết quả cho: {query}. Thử lại #{attempt + 1}")
        except Exception as e:
            logger.error(f"Lỗi tìm kiếm DuckDuckGo lần {attempt + 1}: {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(2)
            else:
                return f"Lỗi hệ thống tìm kiếm sau {MAX_RETRIES} lần thử: {e}"
                
    return f"Không tìm thấy kết quả cho: {query}"


import re

def sanitize_vietnamese_text(text: str) -> str:
    """
    Sanitize text bằng Python trước khi lưu file Markdown.
    Ngăn chặn tuyệt đối Language Bleeding và Category Hallucination.
    """
    # 1. Zero tolerance for CJK characters (Tiếng Trung, Nhật, Hàn)
    # \u4e00-\u9fff: Chinese, \u3040-\u30ff: Japanese, \uac00-\ud7af: Korean
    cjk_pattern = re.compile(r'[\u4e00-\u9fff\u3040-\u30ff\uac00-\ud7af]')
    if cjk_pattern.search(text):
        logger.warning("🚨 [SANITIZER] Phát hiện ký tự ngoại lai (Tiếng Trung/Nhật/Hàn). Đang tiến hành loại bỏ...")
        text = cjk_pattern.sub('', text)

    # 2. Xóa bỏ Category Hallucinations
    # Tra cứu các model hợp lệ đang có trong DB
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT model_name FROM sales ORDER BY units_sold DESC LIMIT 1")
            top_model = cursor.fetchone()
            fallback_model = top_model[0] if top_model else "Galaxy S26 Ultra"
            
        generic_categories = ['Điện tử', 'Thời trang', 'Hàng gia dụng', 'Smartphone', 'Electronics', 'Thiết bị điện tử']
        for cat in generic_categories:
            if cat in text or cat.lower() in text.lower():
                logger.warning(f"🚨 [SANITIZER] Phát hiện danh mục chung '{cat}'. Force-revert về model_name...")
                # Repalce with the top actual model name just to break the hallucination
                # case-insensitive replace
                pattern = re.compile(re.escape(cat), re.IGNORECASE)
                text = pattern.sub(f"{fallback_model} (Sanitized from '{cat}')", text)

    except Exception as e:
        logger.error(f"[SANITIZER] Lỗi khi xử lý category: {e}")

    return text


def save_report(content: str, filename: str):
    """Lưu báo cáo xuống định dạng Markdown (.md) an toàn."""
    try:
        # Chạy sanitizer chặn đứng hallucination
        content = sanitize_vietnamese_text(content)
        
        # Sanitize filename
        filename = os.path.basename(filename)
        full_path = PROCESSED_DATA_DIR / filename
        
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
        
        logger.info(f"Báo cáo đã được lưu: {full_path}")
        return f"Báo cáo đã được lưu thành công tại: {full_path}"
    except Exception as e:
        logger.error(f"Lỗi lưu báo cáo: {e}")
        return f"❌ Lỗi lưu báo cáo: {e}"


def create_sales_chart(data_json: str, chart_name: str = "sales_report.png", y_col: str = "units_sold"):
    """
    Chuyển đổi dữ liệu JSON từ SQL thành biểu đồ cột (Bar Chart).
    """
    logger.info(f"Đang vẽ biểu đồ {chart_name} cho cột {y_col}")
    try:
        try:
            df = pd.read_json(io.StringIO(data_json))
        except Exception as e:
            logger.error(f"Dữ liệu JSON vẽ biểu đồ không hợp lệ: {e}")
            return "❌ Lỗi: Dữ liệu truyền vào vẽ biểu đồ không phải JSON hợp lệ. Hãy gọi SQL query trước."

        if 'model_name' not in df.columns or y_col not in df.columns:
            logger.warning(f"JSON thiếu cột yêu cầu. Hiện có: {list(df.columns)}")
            return f"❌ Lỗi: Thiếu cột 'model_name' hoặc '{y_col}'."

        plt.figure(figsize=(10, 6))
        color = 'skyblue' if y_col == 'units_sold' else 'orange'
        y_label = 'Số lượng bán' if y_col == 'units_sold' else 'Doanh thu (VNĐ)'
        
        plt.bar(df['model_name'], df[y_col], color=color)
        plt.title(f'Phân tích {y_label}')
        plt.xlabel('Model')
        plt.ylabel(y_label)
        plt.xticks(rotation=45)
        plt.tight_layout()

        output_path = PROCESSED_DATA_DIR / chart_name
        plt.savefig(output_path)
        plt.close()
        
        logger.info(f"Đã lưu biểu đồ thành công: {output_path}")
        return f"✅ Biểu đồ đã được lưu tại: {output_path}"
    except Exception as e:
        plt.close()
        logger.error(f"Lỗi vẽ biểu đồ: {e}")
        return f"❌ Lỗi vẽ biểu đồ: {str(e)}"


def read_marketing_content(dummy_arg: str = "") -> str:
    """Đọc toàn bộ nội dung trong thư mục data/raw/marketing_content/ (.txt)"""
    logger.info("Đang đọc dữ liệu marketing nội bộ.")
    content_dir = RAW_DATA_DIR / "marketing_content"
    
    if not content_dir.exists():
        logger.warning(f"Thư mục Content không tồn tại: {content_dir}")
        return f"❌ Thông tin: Thư mục {content_dir} hiện trống hoặc chưa được khởi tạo."
    
    result = []
    try:
        for file in os.listdir(content_dir):
            if file.endswith(".txt"):
                path = content_dir / file
                with open(path, "r", encoding="utf-8") as f:
                    result.append(f"--- NỘI DUNG FILE: {file} ---\n" + f.read().strip() + "\n")
        
        return "\n".join(result) if result else "Tra về chuỗi rỗng vì không có file nào."
    except Exception as e:
        logger.error(f"Lỗi đọc file content: {e}")
        return f"❌ Lỗi hệ thống khi đọc dữ liệu: {e}"


# --- Đóng gói CrewAI tools ---
search_internet = tool(search_internet)
read_marketing_content = tool(read_marketing_content)
save_report = tool(save_report)
create_sales_chart = tool(create_sales_chart)


# --- 4. TRUY VẤN DATABASE (PARAMETRIZED QUERIES) ---

class EnterpriseDataTools:
    def __init__(self, db_path=None):
        self.db_path = str(db_path or DATABASE_PATH)

    def query_marketing_db(self, query: str, output_format: str = "markdown"):
        """
        Truy vấn SQLite marketing_intelligence.db với cơ chế bảo mật Production.
        """
        # Lớp bảo vệ 1: Chỉ cho phép SELECT
        normalized = query.strip().upper()
        if not normalized.startswith("SELECT"):
            logger.warning(f"Phát hiện truy vấn không hợp lệ: {query}")
            return "❌ Bảo mật: Chỉ cho phép câu lệnh xem dữ liệu (SELECT)."

        logger.info(f"Thực thi truy vấn SQL: {query[:100]}...")
        
        try:
            # Lớp bảo vệ 2: Database-level Read-Only & Context Management
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("PRAGMA query_only = ON")
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Để hỗ trợ LLM linh hoạt hơn nhưng vẫn an toàn, 
                # chúng ta thực hiện rà soát các từ khóa nguy hiểm
                forbidden = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "TRUNCATE"]
                if any(word in normalized for word in forbidden):
                    logger.warning(f"Phát hiện từ khóa nguy hiểm trong SQL: {query}")
                    return "❌ Bảo mật: Phát hiện từ khóa bị cấm."

                cursor.execute(query) # SQL Injection protection as this is read-only schema
                rows = cursor.fetchall()

            if not rows:
                logger.info("Truy vấn SQL không trả về kết quả.")
                return "❌ Thông tin: Không tìm thấy dữ liệu phù hợp trong SQL doanh nghiệp."

            columns = rows[0].keys()

            if output_format.lower() == "json":
                return json.dumps([dict(row) for row in rows], ensure_ascii=False)

            # Mặc định: Trả về định dạng Markdown Table
            header = "| " + " | ".join(columns) + " |"
            separator = "| " + " | ".join(["---"] * len(columns)) + " |"
            body = "\n".join(["| " + " | ".join(map(str, row)) + " |" for row in rows])
            return f"\n{header}\n{separator}\n{body}\n"

        except sqlite3.OperationalError as e:
            err = str(e).lower()
            logger.error(f"Lỗi vận hành SQL: {err}")
            # Giải pháp hướng dẫn cho AI Agent
            if "no such column: model" in err: return "Lỗi: Dùng 'model_name' thay vì 'model'."
            if "no such column: price" in err: return "Lỗi: Dùng 'unit_price' hoặc 'current_price'."
            return f"❌ Lỗi SQL: {err}"
        except Exception as e:
            logger.error(f"Lỗi hệ thống SQL không xác định: {e}")
            return f"❌ Lỗi hệ thống SQL: {str(e)}"


# ---------------------------------------------------------------------------
# 5. SIGNAL UPDATE TOOL — Feedback Loop for Continuous Learning
# ---------------------------------------------------------------------------

class SignalUpdateTool(BaseTool):
    """
    Công cụ ghi nhận các bài học chiến lược (Learning Signals) sau mỗi chu kỳ pipeline.
    Cho phép hệ thống tích lũy tri thức theo thời gian, phục vụ vòng lặp cải tiến liên tục.
    """
    name: str = "signal_update"
    description: str = (
        "Ghi nhận một bài học chiến lược (Learning Signal) vào database. "
        "Sử dụng công cụ này để lưu lại các nhận định quan trọng sau mỗi báo cáo, "
        "ví dụ: kênh marketing hiệu suất thấp, sản phẩm cần tái định vị, "
        "hoặc xu hướng thị trường mới cần theo dõi. "
        "Tham số: insight_type (ví dụ: 'low_performer', 'budget_realloc', 'trend_alert', 'content_adjustment') "
        "và learning_content (mô tả chi tiết bài học)."
    )
    db_path: str = Field(default_factory=lambda: str(DATABASE_PATH))

    def _ensure_table(self) -> None:
        """Tạo bảng learning_signals nếu chưa tồn tại."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS learning_signals (
                        id               INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp        TEXT NOT NULL,
                        insight_type     TEXT NOT NULL,
                        learning_content TEXT NOT NULL
                    )
                """)
                conn.commit()
        except Exception as e:
            logger.error(f"Lỗi khi tạo bảng learning_signals: {e}")
            raise

    def _run(self, insight_type: str = "general", learning_content: str = "") -> str:
        """
        Ghi một bài học chiến lược vào bảng learning_signals.
        """
        if not learning_content.strip():
            return "❌ Lỗi: learning_content không được để trống."

        try:
            self._ensure_table()
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT INTO learning_signals (timestamp, insight_type, learning_content) VALUES (?, ?, ?)",
                    (timestamp, insight_type.strip(), learning_content.strip()),
                )
                conn.commit()

            logger.info(f"✅ Signal Update: [{insight_type}] {learning_content[:80]}...")
            return (
                f"✅ Bài học chiến lược đã được ghi nhận thành công.\n"
                f"   Thời gian: {timestamp}\n"
                f"   Loại: {insight_type}\n"
                f"   Nội dung: {learning_content[:120]}..."
            )
        except Exception as e:
            logger.error(f"Lỗi ghi Signal Update: {e}")
            return f"❌ Lỗi hệ thống khi ghi bài học: {str(e)}"