import os
import pandas as pd
from ddgs import DDGS
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import sqlite3
from dotenv import load_dotenv

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

def read_sales_data(file_path: str):
    """Đọc dữ liệu từ file CSV để phân tích báo cáo."""
    try:
        df = pd.read_csv(file_path)
        return df.to_string()
    except Exception as e:
        return f"Lỗi không đọc được file: {e}"

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
        target_folder_id = folder_id or os.getenv("GOOGLE_DOCS_FOLDER_ID")
        
        if not target_folder_id:
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
                flow = InstalledAppFlow.from_client_secrets_file(cred_path, SCOPES)
                creds = flow.run_local_server(port=0)
            with open(token_path, 'w') as token:
                token.write(creds.to_json())

        docs_service = build('docs', 'v1', credentials=creds)
        drive_service = build('drive', 'v3', credentials=creds)
        
        file_metadata = {
            'name': title,
            'mimeType': 'application/vnd.google-apps.document',
            'parents': [target_folder_id]
        }
        
        file = drive_service.files().create(body=file_metadata, fields='id').execute()
        doc_id = file.get('id')
        
        requests = [{'insertText': {'location': {'index': 1}, 'text': content}}]
        docs_service.documents().batchUpdate(documentId=doc_id, body={'requests': requests}).execute()
        
        url = f"https://docs.google.com/document/d/{doc_id}/edit"
        return f"✅ Đã đẩy lên Google Docs thành công: {url}"
        
    except Exception as e:
        return f"❌ Lỗi: {str(e)}"

# Đóng gói thành CrewAI tools
if tool:
    search_internet = tool(search_internet)
    read_sales_data = tool(read_sales_data)
    save_report = tool(save_report)
    publish_to_google_docs = tool(publish_to_google_docs)

# --- 3. CÁC LỚP TIỆN ÍCH ---

class MarketingTools:
    @staticmethod
    def search_internet(query: str):
        return search_internet.run(query) if hasattr(search_internet, "run") else search_internet(query)

    @staticmethod
    def read_sales_data(file_path: str):
        return read_sales_data.run(file_path) if hasattr(read_sales_data, "run") else read_sales_data(file_path)

    @staticmethod
    def save_report(content: str, filename: str):
        return save_report.run(content=content, filename=filename) if hasattr(save_report, "run") else save_report(content=content, filename=filename)

class CloudPublishTools:
    @staticmethod
    def publish_to_docs(title: str, content: str, folder_id: str = ""):
        return publish_to_google_docs.run(title=title, content=content, folder_id=folder_id) if hasattr(publish_to_google_docs, "run") else publish_to_google_docs(title=title, content=content, folder_id=folder_id)

class EnterpriseDataTools:
    def __init__(self, db_path=None):
        if db_path is None:
            src_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(src_dir)
            # TRỎ VÀO DATABASE MARKETING MỚI
            self.db_path = os.path.join(project_root, "data", "raw", "marketing_intelligence.db")
        else:
            self.db_path = db_path
    
    def query_marketing_db(self, query: str):
        """
        Truy vấn database Marketing Intelligence (đối thủ, chiến dịch, cảm xúc khách hàng, doanh số).
        Các bảng có sẵn: competitor_products, marketing_campaigns, social_sentiment, sales_performance, sales.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            conn.close()
            
            if not rows: return "Không tìm thấy dữ liệu phù hợp."
            result = "\n".join([", ".join(map(str, row)) for row in rows])
            return f"Cột: {', '.join(columns)}\n{result}"
        except Exception as e:
            return f"Lỗi truy vấn: {str(e)}"