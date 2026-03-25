try:
    from crewai import Task
    from textwrap import dedent
except ImportError as e:
    print(f"Warning: Could not import required modules for tasks: {e}")
    Task = None
    dedent = lambda x: x  # fallback

class MarketingTasks:

    def research_task(self, agent, market_topic):
        if Task is None:
            return None
        
        return Task(
            description=dedent(f""" 
                Phân tích tình hình thị trường cho chủ đề: {market_topic}.
                Là đại lý bán lẻ, hãy tìm hiểu: 
                1. Giá bán của các bên đối thủ (TGDD, CellphoneS, Apple Store VN).
                2. Các chương trình khuyến mãi lớn mà họ đang áp dụng.
                3. Các dòng máy mới sắp về mà đại lý nên cân nhắc nhập hàng.
            """),
            expected_output="Bản tóm tắt giá đối thủ, danh sách khuyến mãi hot của thị trường và gợi ý dòng sản phẩm nên nhập.",
            agent=agent
        )

    def content_creation_task(self, agent):
        if Task is None:
            return None
            
        return Task(
            description=dedent("""
                Thiết kế chương trình thu hút khách hàng cho chuỗi cửa hàng:
                1. Phân tích social_sentiment: Cảm xúc (top_emotion) nào đang chủ đạo (Skeptical về giá hay Excited về AI)?
                2. Đề xuất 3 mẫu quảng cáo Facebook tập trung vào: Gói bảo hành mở rộng, Thu cũ đổi mới, hoặc Trả góp 0%.
                3. Đề xuất 1 sự kiện trải nghiệm máy ngay tại cửa hàng (Roadshow hoặc Workshop).
            """),
            expected_output="Kế hoạch marketing bán lẻ chi tiết kèm 3 mẫu caption và 1 kịch bản sự kiện store.",
            agent=agent
        )

    def analytics_report_task(self, agent):
        if Task is None:
            return None
            
        return Task(
            description=dedent("""
                Viết Báo cáo Hiệu quả Vận hành Bán lẻ (Executive Retail Report).
                Báo cáo PHẢI dùng dữ liệu thật từ SQL, không bịa số. Định dạng: Markdown.

                YÊU CẦU NỘI DUNG:
                1. Phân tích Doanh số: Tỷ trọng các dòng máy bán chạy (Sử dụng bảng SQL sales).
                2. Hiệu quả Chiến dịch: Chiến dịch nào tại store/online có ROI tốt nhất trong bảng marketing_campaigns?
                3. Hành vi Phân khúc: Khách Gen Z thường mua dòng nào và thanh toán ra sao?
                4. Chiến lược Hành động: Dự kiến nhập thêm model nào? Nên giảm giá mẫu nào để xả kho?

                TRỰC QUAN & XUẤT BẢN:
                - Gọi 'create_sales_chart' để vẽ biểu đồ doanh số.
                - Sau khi xong, gọi 'publish_to_google_docs' để đẩy lên Google Drive.
            """),
            expected_output="Báo cáo chiến lược vận hành bán lẻ đầy đủ biểu đồ, ĐÃ ĐƯỢC XUẤT BẢN lên Google Docs.",
            agent=agent
        )
