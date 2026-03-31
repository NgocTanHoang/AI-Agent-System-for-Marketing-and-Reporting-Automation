import os
import json
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import io
import time
from ddgs import DDGS
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


def save_report(content: str, filename: str):
    """Lưu báo cáo xuống định dạng Markdown (.md) an toàn."""
    try:
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