# AI Marketing Intelligence & Reporting Automation

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/CrewAI-Agentic%20Orchestration-red)](https://www.crewai.com/)
[![Intelligence](https://img.shields.io/badge/LLM-Meta--Llama--3.3--70B-purple)](https://www.nvidia.com/en-us/ai/nim/)
[![Backend](https://img.shields.io/badge/FastAPI-Enterprise--Level-009688)](https://fastapi.tiangolo.com/)

**AI Marketing Intelligence Hub** là hệ thống đa tác nhân (Multi-Agent System) tiên tiến, được thiết kế để tự động hóa hoàn toàn quy trình phân tích thị trường, đối chiếu dữ liệu doanh nghiệp và xây dựng kế hoạch truyền thông chiến lược. Hệ thống giải quyết triệt để bài toán sai lệch dữ liệu trong AI (Data Hallucination) bằng cơ chế **Data Grounding** trực tiếp vào hệ quản trị cơ sở dữ liệu doanh nghiệp.

---

## 🚀 Tính năng cốt lõi (Key Features)

### 1. Agentic Workflow Orchestration
Sử dụng framework **CrewAI** để điều phối luồng làm việc tuần tự (Sequential) giữa 3 Agent chuyên biệt: Research Analyst, Content Strategist và Business Reporter. Mỗi Agent sở hữu Persona và bộ công cụ (Tools) riêng biệt để tối ưu hóa hiệu suất xử lý.

### 2. Data Grounding & SQL Integration
Hệ thống không chỉ dừng lại ở việc tạo văn bản (Generative AI) mà còn tham chiếu trực tiếp dữ liệu thực tế từ SQLite.
*   **Tính toán chuẩn xác**: Tự động truy vấn và tổng hợp ROI (Return on Investment), CPA (Cost Per Acquisition) và Doanh thu thực (Revenue) theo thời gian thực.
*   **Zero Hallucination**: Ràng buộc AI phải sử dụng đúng định dạng tiền tệ (VNĐ) và các khu vực địa lý hợp lệ (`North, South, Central, Highlands`).

### 3. Đối sánh sản phẩm & Competitive Intelligence
Tự động quét và phân tích thông số kỹ thuật (Spec-sheet) của Ta và Đối thủ (Apple, Samsung, Xiaomi...) để nhận diện **lợi thế cạnh tranh** và các điểm hạn chế (Weaknesses) nhằm tối ưu hóa thông điệp tiếp thị.

### 4. Gen Z Marketing Engine
Khả năng chuyển đổi các số liệu tài chính khô khan thành nội dung mạng xã hội (Facebook, TikTok, Instagram) chuẩn mô hình **AIDA**, sử dụng ngôn ngữ hiện đại, thu hút nhưng vẫn đảm bảo tính chiến lược và đúng định hướng thương hiệu.

### 5. High-Tech Interactive Dashboard
Tích hợp giao diện **FastAPI** chuyên nghiệp, hỗ trợ trình diễn báo cáo định dạng Markdown và trực quan hóa dữ liệu qua biểu đồ động (Chart.js), mang lại trải nghiệm người dùng tối ưu cho bộ phận điều hành (Executives).

---

## 🛠️ Công nghệ sử dụng (Tech Stack)

*   **LLM Orchestration**: [CrewAI](https://crewai.com) (Điều phối Agent).
*   **Mô hình ngôn ngữ lớn (LLM)**: Meta-Llama-3.3-70B-Instruct (NVIDIA NIM / OpenRouter).
*   **Backend Framework**: FastAPI (Phát triển API và Web Server).
*   **Cơ sở dữ liệu**: SQLite (Lưu trữ dữ liệu kinh doanh và hiệu suất).
*   **Frontend**: Vanilla HTML5, CSS3 (Google Stitch Design Style), Chart.js (Trực quan hóa).
*   **Công cụ tích hợp**: DuckDuckGo Search API, Custom SQL Intelligence Tools.

---

## 🧠 Kiến trúc tác nhân (Agent Architecture)

1.  **Search Analyst (Intelligence Lead)**: Chịu trách nhiệm nghiên cứu thị trường, thu thập dữ liệu cạnh tranh và thực hiện phân tích đối sánh (Benchmarking).
2.  **Content Strategist (Creative Lead)**: Hoạch định chiến lược nội dung, chuyển hóa các kết quả nghiên cứu thành thông điệp truyền thông theo mô hình AIDA.
3.  **Business Reporter (Strategic Lead)**: Hợp nhất các luồng dữ liệu, thực hiện báo cáo hiệu suất tài chính và đề xuất kế hoạch triển khai chi tiết kèm phân bổ ngân sách.

---

## 🛡️ Tính toàn vẹn dữ liệu (Data Integrity)

Hệ thống áp dụng các quy tắc nghiệp vụ chặt chẽ để đảm bảo sự đồng bộ 100% giữa Dashboard và Logic AI:
*   **SQL Summation Logic**: Doanh thu luôn được tính bằng `SUM(units_sold * unit_price)` từ bảng sales thực tế.
*   **Geographic Constraint**: Khóa cứng phạm vi hoạt động trong 4 khu vực (`North, South, Central, Highlands`), loại bỏ hoàn toàn các khu vực tự phát sinh.
*   **Numerical Formatting**: Ép kiểu định dạng tiền tệ VNĐ (ví dụ: `48,000,000,000 VNĐ`) để đảm bảo tính chuyên nghiệp trong báo cáo tài chính.

---

## ⚙️ Hướng dẫn triển khai (Installation)

### 1. Chuẩn bị môi trường
Yêu cầu Python 3.10 trở lên.
```powershell
git clone <repository-url>
cd "01_AI Agent System for Marketing and Reporting Automation"
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Thiết lập cấu hình
Tạo file `.env` tại thư mục gốc và cung cấp API Key:
```env
OPENROUTER_API_KEY=your_api_key_here
# Hoặc NVIDIA_NIM_API_KEY nếu sử dụng NVIDIA NIM
```

### 3. Thực thi hệ thống
```powershell
python src/init_db.py  # Khởi tạo dữ liệu mẫu
python main.py         # Khởi chạy quy trình AI Agent để tạo báo cáo
uvicorn app:app --reload --port 8000 # Mở Dashboard Quản trị
```
Truy cập: `http://localhost:8000`

---

> [!IMPORTANT]
> Dự án này không chỉ là một ứng dụng AI đơn thuần, mà là một hệ thống **Business Intelligence thế hệ mới**, nơi AI thực sự làm việc dựa trên số liệu kinh doanh cốt lõi của doanh nghiệp.

**Tác giả**: [Ngọc Tân Hoàng](https://github.com/NgocTanHoang)
**Phiên bản**: 3.0.0 - *Enterprise Readiness*
