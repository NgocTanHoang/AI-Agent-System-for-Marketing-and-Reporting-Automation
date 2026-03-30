import os
import json
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import io
from ddgs import DDGS
from dotenv import load_dotenv

# --- 0. CẤU HÌNH ĐƯỜNG DẪN ---
SRC_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SRC_DIR)
CONFIG_DIR = os.path.join(PROJECT_ROOT, "config")

load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

# --- 1. KHỞI TẠO DECORATOR ---
try:
    from crewai.tools import tool
except ImportError:
    try:
        from crewai import tool
    except ImportError:
        raise ImportError(
            "Không thể import CrewAI tool decorator. "
            "Kiểm tra lại cài đặt: pip install crewai[tools]"
        )


# --- 2. CÁC HÀM STANDALONE ---

def search_internet(query: str):
    """Quét internet để lấy tin tức mới nhất về xu hướng công nghệ hoặc đối thủ."""
    print(f"--- Đang săn tin với từ khóa: {query} ---")
    try:
        ddgs_client = DDGS()
        results = list(ddgs_client.text(query, max_results=5))
        return results if results else f"Không tìm thấy kết quả cho: {query}"
    except Exception as e:
        return f"Lỗi tìm kiếm: {e}"


def save_report(content: str, filename: str):
    """Lưu báo cáo xuống định dạng Markdown (.md). Tool này chỉ dùng để lưu file vật lý. 
    LƯU Ý: Nếu bạn là Agent cuối cùng, bạn VẪN PHẢI trả về toàn bộ nội dung báo cáo như là Câu trả lời cuối cùng (Final Answer).
    """
    output_dir = os.path.join(PROJECT_ROOT, "data", "processed")
    os.makedirs(output_dir, exist_ok=True)

    filename = os.path.basename(filename)
    full_path = os.path.join(output_dir, filename)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)
    return f"Báo cáo đã được lưu thành công tại: {full_path}"



def create_sales_chart(data_json: str, chart_name: str = "sales_report.png", y_col: str = "units_sold"):
    """
    Chuyển đổi dữ liệu JSON từ SQL thành biểu đồ cột (Bar Chart) để trực quan hóa.
    - data_json: Dữ liệu JSON chứa cột 'model_name' và y_col.
    - y_col: Cột dữ liệu dùng để vẽ Y-axis ('units_sold' hoặc 'revenue').
    - chart_name: Tên file xuất ra (Vd: top_revenue.png)
    """
    try:
        try:
            df = pd.read_json(io.StringIO(data_json))
        except ValueError:
            return (
                "❌ Lỗi: Dữ liệu truyền vào tool vẽ biểu đồ KHÔNG phải là JSON hợp lệ. "
                "Hãy gọi 'query_marketing_db(query, output_format=\"json\")' đầu tiên để lấy mảng JSON rồi truyền mảng đó vào đây."
            )

        if 'model_name' not in df.columns or y_col not in df.columns:
            return f"❌ Lỗi: JSON thiếu cột 'model_name' hoặc '{y_col}'. Các cột hiện có: {list(df.columns)}"

        plt.figure(figsize=(10, 6))
        color = 'skyblue' if y_col == 'units_sold' else 'orange'
        y_label = 'Số lượng bán' if y_col == 'units_sold' else 'Doanh thu (VNĐ)'
        plt.bar(df['model_name'], df[y_col], color=color)
        plt.title(f'Biểu đồ theo {y_label}')
        plt.xlabel('Model')
        plt.ylabel(y_label)
        plt.xticks(rotation=45)
        plt.tight_layout()

        output_dir = os.path.join(PROJECT_ROOT, "data", "processed")
        os.makedirs(output_dir, exist_ok=True)

        output_path = os.path.join(output_dir, chart_name)
        plt.savefig(output_path)
        plt.close()
        return (
            f"✅ Biểu đồ đã được lưu tại: {output_path}. "
            f"Hãy chèn vào báo cáo bằng cú pháp Markdown: ![Chart]({output_path})"
        )
    except Exception as e:
        plt.close()
        return f"❌ Lỗi vẽ biểu đồ: {str(e)}"


def read_marketing_content(dummy_arg: str = "") -> str:
    """Đọc toàn bộ nội dung trong thư mục data/raw/marketing_content/ (.txt)
    Lấy ra các bài viết content nháp và review của KOLs để phân tích, phản biện và ra quyết định.
    """
    print("--- Đang đọc các bài marketing thô ---")
    content_dir = os.path.join(PROJECT_ROOT, "data", "raw", "marketing_content")
    if not os.path.exists(content_dir):
        return f"❌ Lỗi: Không tìm thấy thư mục {content_dir}"
    
    result = []
    for file in os.listdir(content_dir):
        if file.endswith(".txt"):
            path = os.path.join(content_dir, file)
            with open(path, "r", encoding="utf-8") as f:
                result.append(f"--- NỘI DUNG FILE: {file} ---\n" + f.read().strip() + "\n")
    
    return "\n".join(result) if result else "Tra về chuỗi rỗng vì không có file nào."


# --- Đóng gói thành CrewAI tools ---
search_internet = tool(search_internet)
read_marketing_content = tool(read_marketing_content)
save_report = tool(save_report)
create_sales_chart = tool(create_sales_chart)




# --- 4. TRUY VẤN DATABASE (READ-ONLY, CHỐNG SQL INJECTION) ---

class EnterpriseDataTools:
    def __init__(self, db_path=None):
        if db_path is None:
            self.db_path = os.path.join(PROJECT_ROOT, "data", "raw", "marketing_intelligence.db")
        else:
            self.db_path = db_path

    def query_marketing_db(self, query: str, output_format: str = "markdown"):
        """
        Truy vấn SQLite marketing_intelligence.db để lấy dữ liệu thực chiến.

        ⚠️ QUY TẮC BẮT BUỘC:
        1. SORT & LIMIT: Luôn sử dụng 'ORDER BY [column] DESC' và 'LIMIT [n]' để lấy dữ liệu dẫn đầu.
        2. Dùng 'model_name' (KHÔNG dùng 'model').
        3. Dùng 'unit_price' trong 'sales' (KHÔNG dùng 'price').
        4. Dùng 'current_price' trong 'competitor_products' (KHÔNG dùng 'price').
        5. DOANH THU: ĐỂ TÌM MODEL DẪN ĐẦU DOANH THU, BẮT BUỘC phải tính tổng `SUM(units_sold * unit_price)` TỪ BẢNG `sales`. Tuyệt đối không dùng bảng `sales_performance` để so sánh xếp hạng doanh thu.

        DANH SÁCH BẢNG & CỘT:
        - sales: (brand, model_name, units_sold, unit_price, region) -> 'region' gồm: North, South, Central, Highlands. -> TÍNH DOANH THU TỪ BẢNG NÀY.
        - competitor_products: (brand, model_name, key_features, current_price, strengths, weaknesses)
        - sales_performance: (model_name, units_sold, revenue, month_period)
        - marketing_campaigns: (campaign_name, channel, budget, reach, conversions, roi, status)
        - social_sentiment: (keyword, positive_score, negative_score, total_mentions, top_complaint)

        VÍ DỤ TOP REVENUE:
        SELECT model_name, SUM(units_sold * unit_price) AS revenue FROM sales GROUP BY model_name ORDER BY revenue DESC LIMIT 1;
        """
        # Lớp bảo vệ 1: Application-level — chỉ cho phép SELECT
        normalized = query.strip().upper()
        if not normalized.startswith("SELECT"):
            return "❌ Lỗi: Chỉ cho phép câu lệnh SELECT. Các lệnh thay đổi dữ liệu không được phép."

        try:
            # Lớp bảo vệ 2: Database-level — PRAGMA query_only
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("PRAGMA query_only = ON")
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(query)
                rows = cursor.fetchall()

            if not rows:
                return "❌ LỖI: Không tìm thấy dữ liệu phù hợp trong SQL. TUYỆT ĐỐI KHÔNG ĐƯỢC tự bịa đặt con số, hãy báo cáo rằng không có thông tin."

            columns = rows[0].keys()

            if output_format.lower() == "json":
                return json.dumps([dict(row) for row in rows], ensure_ascii=False)

            # Mặc định: Trả về định dạng bảng Markdown
            header = "| " + " | ".join(columns) + " |"
            separator = "| " + " | ".join(["---"] * len(columns)) + " |"
            body = "\n".join(["| " + " | ".join(map(str, row)) + " |" for row in rows])
            return f"\n{header}\n{separator}\n{body}\n"

        except sqlite3.OperationalError as e:
            error_msg = str(e)
            error_msg_lower = error_msg.lower()
            
            # Hướng dẫn cụ thể cho các lỗi tên cột hay gặp
            if "no such column: model" in error_msg_lower and "model_name" not in error_msg_lower:
                return "❌ Lỗi SQL: Cột 'model' không tồn tại. Dùng 'model_name'."
            if "no such column: model_name" in error_msg_lower and "marketing_campaigns" in query.lower():
                return "❌ Lỗi SQL: Bảng 'marketing_campaigns' KHÔNG CÓ cột 'model_name'. Dùng 'campaign_name' hoặc join qua qua ID."
            if "no such column: roi" in error_msg_lower:
                return "❌ Lỗi SQL: Cột 'ROI'/'roi' chỉ có trong bảng 'marketing_campaigns'. Query mẫu: SELECT campaign_name, roi FROM marketing_campaigns"
            if "no such column: price" in error_msg_lower:
                return "❌ Lỗi SQL: Cột 'price' không tồn tại. Trong 'sales' dùng 'unit_price'. Trong 'competitor_products' dùng 'current_price'."
            if "no such column: revenue" in error_msg_lower:
                return "❌ Lỗi SQL: Cột 'revenue' chỉ có trong bảng 'sales_performance', KHÔNG có trong 'sales'."
            
            if "no such table" in error_msg_lower:
                return f"❌ Lỗi SQL: {error_msg}. Bảng có sẵn: sales, competitor_products, social_sentiment, marketing_campaigns, sales_performance."
            return f"❌ Lỗi SQL: {error_msg}"
        except Exception as e:
            return f"❌ Lỗi không xác định: {str(e)}"