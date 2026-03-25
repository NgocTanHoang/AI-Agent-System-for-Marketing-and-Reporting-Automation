import os
from ddgs import DDGS
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from dotenv import load_dotenv

# --- 0. CẤU HÌNH ĐƯỜNG DẪN ---
SRC_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SRC_DIR)

load_dotenv()  # Tải biến môi trường từ file .env


# --- 1. KHỞI TẠO DECORATOR ---
try:
    from crewai.tools import tool
except ImportError:
    try:
        from crewai import tool
    except ImportError:
        tool = None

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
    src_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(src_dir)
    output_dir = os.path.join(project_root, "data", "processed")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    filename = os.path.basename(filename)
    full_path = os.path.join(output_dir, filename)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)
    return f"Báo cáo đã được lưu thành công tại: {full_path}"

def publish_to_google_docs(title: str, content: str, folder_id: str = ""):
    """
    Tạo một Google Doc mới trong thư mục được chỉ định.
    Mặc định lấy từ biến môi trường GOOGLE_DOCS_FOLDER_ID.
    """
    try:
        print(f"--- Đang bắt đầu xuất bản báo cáo: {title} ---")
        target_folder_id = folder_id or os.getenv("GOOGLE_DOCS_FOLDER_ID")
        
        if not target_folder_id:
            print("❌ Lỗi: Không có GOOGLE_DOCS_FOLDER_ID")
            return "❌ Lỗi: Không tìm thấy GOOGLE_DOCS_FOLDER_ID trong file .env hoặc tham số truyền vào."

        # Get credentials
        SCOPES = ['https://www.googleapis.com/auth/documents', 'https://www.googleapis.com/auth/drive.file']
        src_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(src_dir)
        token_path = os.path.join(project_root, 'token.json')
        cred_path = os.path.join(project_root, 'credentials.json')

        creds = None
        if os.path.exists(token_path):
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                print("--- Yêu cầu đăng nhập Google (Auth required) ---")
                flow = InstalledAppFlow.from_client_secrets_file(cred_path, SCOPES)
                creds = flow.run_local_server(port=0)
            with open(token_path, 'w') as token:
                token.write(creds.to_json())

        docs_service = build('docs', 'v1', credentials=creds)
        drive_service = build('drive', 'v3', credentials=creds)
        
        print(f"--- Đang tạo file trong folder: {target_folder_id} ---")
        file_metadata = {
            'name': title,
            'mimeType': 'application/vnd.google-apps.document',
            'parents': [target_folder_id]
        }
        
        file = drive_service.files().create(body=file_metadata, fields='id').execute()
        doc_id = file.get('id')
        print(f"--- Đã tạo Doc ID: {doc_id}. Đang cập nhật nội dung... ---")
        
        requests = [{'insertText': {'location': {'index': 1}, 'text': content}}]
        docs_service.documents().batchUpdate(documentId=doc_id, body={'requests': requests}).execute()
        
        url = f"https://docs.google.com/document/d/{doc_id}/edit"
        print(f"✅ Xuất bản thành công: {url}")
        return f"✅ Đã đẩy lên Google Docs thành công: {url}"
        
    except Exception as e:
        print(f"❌ Lỗi khi xuất bản: {str(e)}")
        return f"❌ Lỗi: {str(e)}"

def create_sales_chart(data_json: str, chart_name: str = "sales_report.png"):
    """
    Chuyển đổi dữ liệu JSON từ SQL thành biểu đồ cột (Bar Chart) để trực quan hóa doanh số.
    Dữ liệu JSON đầu vào phải có các cột: 'model_name' và 'units_sold'.
    """
    try:
        # Thử load dữ liệu từ JSON string
        try:
            df = pd.read_json(data_json)
        except ValueError:
            return "❌ Lỗi: Dữ liệu truyền vào tool vẽ biểu đồ KHÔNG phải là JSON hợp lệ. Hãy gọi 'query_marketing_db(query, output_format=\"json\")' trước."
        
        # Kiểm tra cột bắt buộc
        if 'model_name' not in df.columns or 'units_sold' not in df.columns:
            return f"❌ Lỗi: JSON thiếu cột 'model_name' hoặc 'units_sold'. Các cột hiện có: {list(df.columns)}"

        plt.figure(figsize=(10, 6))
        plt.bar(df['model_name'], df['units_sold'], color='skyblue')
        plt.title('Doanh số Smartphone theo Model')
        plt.xlabel('Model')
        plt.ylabel('Số lượng bán')
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        output_dir = os.path.join(PROJECT_ROOT, "data", "processed")
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        output_path = os.path.join(output_dir, chart_name)
        plt.savefig(output_path)
        plt.close()
        return f"✅ Biểu đồ đã được lưu tại: {output_path}. Hãy chèn vào báo cáo bằng cú pháp Markdown: ![Chart]({output_path})"
    except Exception as e:
        plt.close()
        return f"❌ Lỗi vẽ biểu đồ: {str(e)}"

# Đóng gói thành CrewAI tools
if tool:
    search_internet = tool(search_internet)

    save_report = tool(save_report)
    publish_to_google_docs = tool(publish_to_google_docs)
    create_sales_chart = tool(create_sales_chart)

# --- 3. CÁC LỚP TIỆN ÍCH ---

class MarketingTools:
    @staticmethod
    def search_internet(query: str):
        return search_internet.run(query) if hasattr(search_internet, "run") else search_internet(query)

    @staticmethod
    def save_report(content: str, filename: str):
        return save_report.run(content=content, filename=filename) if hasattr(save_report, "run") else save_report(content=content, filename=filename)

class CloudPublishTools:
    @staticmethod
    def publish_to_docs(title: str, content: str, folder_id: str = ""):
        """
        Đảm bảo tên hàm gọi bên trong khớp với hàm standalone đã định nghĩa.
        Hỗ trợ gọi qua Tool object (.run) hoặc hàm trực tiếp.
        """
        if hasattr(publish_to_google_docs, "run"):
            return publish_to_google_docs.run(title=title, content=content, folder_id=folder_id)
        return publish_to_google_docs(title=title, content=content, folder_id=folder_id)

class EnterpriseDataTools:
    def __init__(self, db_path=None):
        if db_path is None:
            src_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(src_dir)
            # TRỎ VÀO DATABASE MARKETING MỚI
            self.db_path = os.path.join(project_root, "data", "raw", "marketing_intelligence.db")
        else:
            self.db_path = db_path
    
    def query_marketing_db(self, query: str, output_format: str = "markdown"):
        """
        Truy vấn database Marketing Intelligence (sales, competitor_products, sentiment...).
        - output_format: "markdown" (mặc định cho báo cáo) hoặc "json" (để truyền vào tool vẽ biểu đồ).
        Các bảng: competitor_products, marketing_campaigns, social_sentiment, sales_performance, sales.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            # Dùng Row factory để dễ dàng chuyển đổi sang JSON
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()
            
            if not rows: return "Không tìm thấy dữ liệu phù hợp."
            
            columns = rows[0].keys()
            conn.close()
            
            if output_format.lower() == "json":
                import json
                # Chuyển đổi list các Row thành list các dict
                data = [dict(row) for row in rows]
                return json.dumps(data, ensure_ascii=False)
            
            # Mặc định: Trả về định dạng bảng Markdown để báo cáo đẹp hơn
            header = "| " + " | ".join(columns) + " |"
            separator = "| " + " | ".join(["---"] * len(columns)) + " |"
            body = "\n".join(["| " + " | ".join(map(str, row)) + " |" for row in rows])
            return f"\n{header}\n{separator}\n{body}\n"
        except Exception as e:
            return f"Lỗi truy vấn: {str(e)}"