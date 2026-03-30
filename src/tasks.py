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
                1. Dùng tool tìm kiếm để lấy thông số kỹ thuật (Chipset, RAM, Camera, Sạc nhanh) của đối thủ từ bảng 'competitor_products'. Lưu ý: Bảng này dùng 'model_name' và 'current_price'.
                2. Truy vấn bảng 'sales' và 'sales_performance' để xác định chính xác Model nào (gọi tên model_name) đang có tồn kho cao nhất hoặc doanh số thấp nhất theo từng Vùng miền (region). Lưu ý: Dùng cột 'units_sold' và 'revenue'.
                3. XÁC ĐỊNH 'NỖI ĐAU' KHÁCH HÀNG: Đối thủ đang bị chê ở điểm nào? (Ví dụ: iPhone sạc chậm, Samsung nóng máy).
                4. Tìm 03 xu hướng 'Toxic' hoặc 'Flexing' trên TikTok/Facebook mà Gen Z đang sử dụng để làm content.
                
                ⚠️ CẢNH BÁO DATA INTEGRITY: Tuyệt đối không làm tròn số. Khi query, TUYỆT ĐỐI không dùng cột 'model', PHẢI dùng 'model_name'.
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
                   - Mẫu 3 (CTA): Call to action cực gắt kèm deal giảm giá ĐÍCH DANH cho Model đang chậm KPI (Lấy từ research, PHẢI DÙNG TÊN 'model_name' CHÍNH XÁC).
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
                1. DATA INTEGRITY: Trích xuất ROI từ bảng 'marketing_campaigns' (cột 'roi'), Revenue từ 'sales_performance' (cột 'revenue'). Không làm tròn. Lưu ý dùng 'model_name' (KHÔNG dùng 'model').
                2. ĐÍCH DANH MODEL: Gọi tên chính xác model_name có doanh số thấp nhất và đề xuất % giảm giá cụ thể.
                3. PHÂN TÍCH ĐỐI ĐẦU: Dùng Chipset/Camera cụ thể từ competitor_products để chỉ ra tại sao khách hàng chê đối thủ và nên mua máy mình.
                4. PHÂN BỔ NGÂN SÁCH: Chỉ rõ dồn bao nhiêu ngân sách (số tiền cụ thể) vào kênh nào (TikTok/KOL) tại khu vực nào.
                
                QUY TẮC ĐỊNH DẠNG (BẮT BUỘC):
                - SỬ DỤNG Markdown CHUẨN. Mỗi tiêu đề (##) PHẢI nằm trên một dòng riêng.
                - KHÔNG ĐƯỢC viết dính chùm tất cả các mục trên một dòng duy nhất.
                - Sử dụng bảng Markdown (|---|---|) để trình bày số liệu.
                
                BỐ CỤC BÁO CÁO (BẮT BUỘC):
                ## 🚀 CHIẾN LƯỢC HÀNH ĐỘNG TỔNG THỂ & ĐIỀU PHỐI CHIẾN DỊCH
                ## 📊 Hiệu quả Tài chính & Chỉ số ROI (Bảng chi tiết)
                ## ⚖️ Phân tích Cạnh tranh & Đòn bẩy Tính năng
                ## 🎯 Mục tiêu Sản phẩm & Chính sách Ưu đãi đề xuất
                ## 📝 03 Phương án Truyền thông Viral (Tác giả: Content Specialist)
                ## ⚠️ Kế hoạch thực thi 7 ngày (Model - Khu vực - Ngân sách cụ thể)
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
