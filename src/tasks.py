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
        """Bước 1: Tình báo Thực chiến & Benchmarking Đối thủ."""
        return Task(
            description=dedent(f"""
                Thực hiện tình báo thị trường 'sắc lẹm' cho chủ đề: {market_topic}.
                
                QUY TRÌNH BẮT BUỘC:
                1. Dùng tool tìm kiếm để lấy thông số kỹ thuật (Chipset, RAM, Camera, Sạc nhanh) của đối thủ từ bảng 'competitor_products'.
                2. Truy vấn bảng 'sales' để xác định chính xác Model nào đang có tồn kho cao nhất hoặc doanh số thấp nhất theo từng Vùng miền.
                3. XÁC ĐỊNH 'NỖI ĐAU' KHÁCH HÀNG: Đối thủ đang bị chê ở điểm nào? (Ví dụ: iPhone sạc chậm, Samsung nóng máy).
                4. Tìm 03 xu hướng 'Toxic' hoặc 'Flexing' trên TikTok/Facebook mà Gen Z đang sử dụng để làm content.
                
                ⚠️ CẢNH BÁO DATA INTEGRITY: Tuyệt đối không làm tròn số. Nếu giá là 32.190.000 VNĐ, phải báo cáo đúng như vậy.
            """),
            expected_output=dedent("""
                Báo cáo Tình báo (Markdown):
                - Bảng so sánh cấu hình chi tiết (Chip, Camera, Sạc) giữa Ta và Đối thủ.
                - Danh sách 03 Model đang gặp vấn đề doanh số (gọi tên đích danh từ SQL).
                - 03 Buzzwords/Trends Gen Z đang hot nhất (Ví dụ: Check-var, Slay...).
            """),
            agent=agent,
        )

    def content_creation_task(self, agent, research_task: Task):
        """Bước 2: Sáng tạo Nội dung Viral 'Toxic & Flexing'."""
        return Task(
            description=dedent("""
                Đóng vai CSO (Chief Slay Officer) để tạo ra các bài đăng 'cháy phố'.
                
                QUY TRÌNH:
                1. Sử dụng các câu Hook 'Toxic nhẹ' để so sánh sản phẩm của mình với đối thủ. 
                2. Ngôn ngữ: Gen Z thực chiến (Check-var, 32 củ, sạc rùa, đỉnh nóc kịch trần...).
                3. Phải tạo ra 03 mẫu bài đăng cho Facebook/TikTok bằng cấu trúc AIDA:
                   - Mẫu 1 (Pain Point): Nhấn vào nỗi đau của người dùng máy đối thủ.
                   - Mẫu 2 (Flexing): Khoe cấu hình hoặc tính năng độc quyền (Ví dụ: Chụp đêm 'hết nước chấm').
                   - Mẫu 3 (CTA): Call to action cực gắt kèm deal giảm giá đích danh cho Model đang chậm KPI (lấy từ Research).
            """),
            expected_output=dedent("""
                03 Mẫu Bài Đăng 'Slay' nhất:
                - Định dạng: [Tiêu đề] - [Nội dung AIDA] - [CTA] - [10 Hashtags].
                - Phải lồng ghép các từ khóa: Slay, Flex, Check-var, 32 củ.
                - Phải chỉ đích danh model cần đẩy doanh số.
            """),
            agent=agent,
            context=[research_task],
        )

    def marketing_strategy_task(self, agent, research_task: Task, content_task: Task, tools: List[BaseTool]):
        """Bước 3: Mật lệnh Chiến lược Tăng trưởng."""
        return Task(
            description=dedent("""
                Hợp nhất toàn bộ dữ liệu thành một bản 'Mật lệnh' cho Sếp.
                
                YÊU CẦU QUY TRÌNH:
                1. DATA INTEGRITY: Trích xuất ROI, CPA, Revenue lẻ đến từng số lẻ. Không làm tròn.
                2. ĐÍCH DANH MODEL: Gọi tên chính xác Model có doanh số thấp nhất và đề xuất % giảm giá cụ thể.
                3. PHÂN TÍCH ĐỐI ĐẦU: Dùng Chipset/Camera cụ thể từ competitor_products để chỉ ra tại sao khách hàng chê đối thủ và nên mua máy mình.
                4. PHÂN BỔ NGÂN SÁCH: Chỉ rõ dồn bao nhiêu ngân sách (số tiền cụ thể) vào kênh nào (TikTok/KOL) tại khu vực nào.
                
                BỐ CỤC BÁO CÁO (##):
                ## 🚀 MẬT LỆNH HÀNH ĐỘNG & ĐIỀU PHỐI CHIẾN DỊCH
                ## 📊 Hiệu quả Tài chính chi tiết (Bảng Markdown lẻ đến hàng đơn vị)
                ## ⚖️ Phân tích Đối đầu: Dìm hàng đối thủ & Flexing tính năng
                ## 🎯 Target Model & Mức giảm giá đề xuất
                ## 📝 03 Mẫu Post 'Gen Z Toxic' (Copy từ Content Specialist)
                ## ⚠️ Kế hoạch thực thi 7 ngày tới (Model - Khu vực - Ngân sách)
            """),
            expected_output=dedent("""
                BÁO CÁO CHIẾN LƯỢC THỰC CHIẾN (>800 TỪ):
                - KHÔNG ĐƯỢC TRẢ LỜI CHUNG CHUNG. 
                - SỐ LIỆU PHẢI CHÍNH XÁC TUYỆT ĐỐI TỪ SQL.
                - PHẢI CÓ MODEL_NAME VÀ KHU VỰC CỤ THỂ.
                - FINAL ANSWER LÀ TOÀN BỘ NỘI DUNG BÁO CÁO.
            """),
            agent=agent,
            context=[research_task, content_task],
            tools=tools,
        )
