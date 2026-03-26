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
    """Lưu báo cáo xuống định dạng Markdown (.md)."""
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
        Truy vấn database Marketing Intelligence (sales, competitor_products, sentiment...).
        - output_format: "markdown" (mặc định cho báo cáo) hoặc "json" (để truyền vào tool vẽ biểu đồ).
        - Chỉ cho phép câu lệnh SELECT (read-only).
        Các bảng: competitor_products, marketing_campaigns, social_sentiment, sales_performance, sales.
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
                return "Không tìm thấy dữ liệu phù hợp."

            columns = rows[0].keys()

            if output_format.lower() == "json":
                return json.dumps([dict(row) for row in rows], ensure_ascii=False)

            # Mặc định: Trả về định dạng bảng Markdown
            header = "| " + " | ".join(columns) + " |"
            separator = "| " + " | ".join(["---"] * len(columns)) + " |"
            body = "\n".join(["| " + " | ".join(map(str, row)) + " |" for row in rows])
            return f"\n{header}\n{separator}\n{body}\n"

        except sqlite3.OperationalError as e:
            return f"❌ Lỗi SQL: {str(e)}"
        except Exception as e:
            return f"❌ Lỗi không xác định: {str(e)}"