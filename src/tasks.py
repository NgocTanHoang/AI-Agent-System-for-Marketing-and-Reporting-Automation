from typing import List
from textwrap import dedent

try:
    from crewai import Task
    from crewai.tools import BaseTool
except ImportError as e:
    raise ImportError(
        f"Không thể import module CrewAI. Kiểm tra lại cài đặt: {e}"
    )


class MarketingTasks:

    def research_task(self, agent, market_topic: str):
        """Bước 1: Tình báo thị trường & Phân tích Gaps."""
        return Task(
            description=dedent(f"""
                Thực hiện tình báo thị trường chuyên sâu cho chủ đề: {market_topic} trong ngành smartphone.
                
                QUY TRÌNH BẮT BUỘC:
                1. Dùng tool tìm kiếm để lấy GIÁ THỰC TẾ tại TGDD, CellphoneS và Hoàng Hà cho các model {market_topic}.
                2. Truy vấn bảng 'competitor_products' để đối chiếu giá niêm yết của ta với đối thủ.
                3. XÁC ĐỊNH 'PRICE GAP': Model nào đối thủ đang phá giá hoặc có khuyến mãi 'Trade-in' tốt hơn?
                4. Tìm kiếm 03 xu hướng công nghệ (ví dụ: AI Camera, sạc 120W) đang là tiêu chí chọn mua hàng đầu hiện nay.

                YÊU CẦU TRÌNH BÀY:
                - Bảng so sánh giá: Model | Giá Đối Thủ | Giá Của Ta | Chênh lệch.
                - Mục 'Nhận định Gaps': Phải ghi rõ 'Ta đang mất lợi thế ở dòng X vì đối thủ Y đang tặng kèm Z'.
            """),
            expected_output=dedent("""
                Báo cáo tình báo (Markdown):
                - Bảng so sánh giá đối thủ chi tiết.
                - Phân tích 03 điểm Gaps chiến lược.
                - Danh sách dẫn nguồn (URL) từ Internet.
            """),
            agent=agent,
        )

    def content_creation_task(self, agent, research_task: Task):
        """Bước 2: Kiểm toán Nội dung (Content Audit) - Đối chiếu Sự thật vs. Quảng cáo."""
        return Task(
            description=dedent("""
                Tiến hành 'Kiểm toán nội dung' (Audit) cho Team Marketing. 
                Nhiệm vụ của bạn là trở thành một người phản biện 'khó tính' dựa trên dữ liệu.

                QUY TRÌNH:
                1. Đọc file nháp (.txt) dùng 'read_marketing_content'.
                2. Truy vấn 'social_sentiment' để lấy Top 03 phàn nàn của khách hàng về model tương ứng.
                3. KIỂM TRA TÍNH TRUNG THỰC: 
                   - Nếu Marketing nói 'Pin trâu' mà Social nói 'Nhanh nóng máy', hãy chỉ trích sự thiếu trung thực.
                   - Nếu Marketing bỏ qua điểm yếu về giá mà đối thủ đang thắng (từ Research Task), hãy yêu cầu bổ sung chiến lược 'Quà tặng' để bù đắp.

                YÊU CẦU ĐẦU RA:
                - Bảng 'Đối chiếu Sự thật': [Nội dung Marketing nói] vs [Sự thật từ Database].
                - Đề xuất sửa đổi: Viết lại 02 đoạn văn quan trọng nhất của bài bài viết theo hướng trung thực nhưng vẫn hấp dẫn.
                Always cite specific numbers from the database.
            """),
            expected_output=dedent("""
                Bản kiểm toán nội dung chuyên sâu:
                - Bảng đối chiếu thực tế (Truth vs. Draft).
                - Điểm đánh giá mức độ rủi ro truyền thông (1-10).
                - Bản thảo Key Messages đã sửa đổi.
            """),
            agent=agent,
            context=[research_task],
        )

    def analytics_report_task(self, agent, research_task: Task, content_task: Task, tools: List[BaseTool]):
        """Bước 3: Báo cáo Executive - Tính toán KPI thực và Đề xuất."""
        return Task(
            description=dedent("""
                Tổng hợp báo cáo Executive Retail Report dành cho cấp quản trị. 
                Báo cáo này PHẢI dựa trên các con số thực tế từ SQL. KHÔNG ĐƯỢC tự bịa số liệu.

                QUY TRÌNH TỐI QUAN TRỌNG:
                1. Dùng 'query_marketing_db' truy vấn bảng 'sales_performance' để lấy TỔNG DOANH THU thực tế (đơn vị tỷ VNĐ).
                2. Truy vấn bảng 'marketing_campaigns' để lấy TỔNG NGÂN SÁCH (budget).
                3. TÍNH TOÁN CHÍNH XÁC:
                   - ROI = (Tổng Doanh Thu - Tổng Ngân Sách) / Tổng Ngân Sách. (Ví dụ: Doanh thu 1000 tỷ, Ngân sách 1 tỷ -> ROI x1000).
                   - CPA = Tổng Ngân Sách / Tổng Conversions.
                4. CẢNH BÁO: Dữ liệu thật doanh thu iPhone 17 Pro là ~480 tỷ VNĐ. Nếu bạn báo cáo 10 triệu là SAI HOÀN TOÀN.

                YÊU CẦU VẼ BIỂU ĐỒ (Bắt buộc):
                1. Top 5 Doanh Thu (y_col="revenue").
                2. Top 5 Doanh Số (y_col="units_sold").

                CẤU TRÚC BÁO CÁO:
                - # 📱 BÁO CÁO CHIẾN LƯỢC KINH DOANH SMARTPHONE Q1/2026
                - ## 📈 Hiệu suất Tài chính: Bảng Markdown với các cột: Chỉ số | Giá trị | Đơn vị. 
                - Chèn link ảnh: ![Top Doanh Thu](data/processed/top_revenue.png)
                - ## ⚠️ Cảnh báo & Hành động: Chơi chữ ít, tập trung vào số liệu.
            """),
            expected_output=dedent("""
                Một bản báo cáo Markdown chuyên nghiệp (500+ từ):
                - TRÌNH BÀY SỐ LIỆU DOANH THU THEO ĐƠN VỊ TỶ VNĐ (Vd: 480 tỷ VNĐ).
                - Nhúng đầy đủ 2 biểu đồ PNG đã tạo.
                - Phân tích sâu sắc dựa trên Price Gap từ Research Task và Truth vs Draft từ Content Task.
                - KHÔNG ĐƯỢC dùng số giả 10.000.000 cho doanh thu.
            """),
            agent=agent,
            context=[research_task, content_task],
            tools=tools,
        )
