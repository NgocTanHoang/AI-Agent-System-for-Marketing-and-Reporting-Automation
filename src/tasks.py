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
        """Bước 1: Trend Scouting & Phân tích Insight Đối thủ."""
        return Task(
            description=dedent(f"""
                Thực hiện tình báo thị trường chuyên sâu cho chủ đề: {market_topic} trong ngành smartphone.
                
                QUY TRÌNH BẮT BUỘC:
                1. Dùng tool tìm kiếm để lấy thông tin về các 'Viral Trends' và 'Chiến dịch thành công của đối thủ' (như TGDD, CellphoneS, Hoàng Hà) cho các model {market_topic}.
                2. Truy vấn bảng 'competitor_products' để đối chiếu giá niêm yết của ta với đối thủ.
                3. XÁC ĐỊNH MỤC TIÊU MARKETING: Đối thủ đang dùng thông điệp gì để bán hàng? (Ví dụ: Khuyến mãi Trade-in, AI Camera test).
                4. Tìm kiếm 03 xu hướng nội dung (ví dụ: Video ngắn TikTok biến hình, Bài đăng Meme hài hước về pin) đang được Gen Z tương tác nhiều nhất.

                YÊU CẦU TRÌNH BÀY:
                - Danh sách 03 Viral Trends hiện tại.
                - Phân tích góc nhìn chiến dịch đối thủ (Thông điệp & Giá).
                - Nhận định Gaps nội dung: Cửa hàng của chúng ta đang thiếu loại nội dung nào để thu hút khách hàng?
            """),
            expected_output=dedent("""
                Báo cáo xu hướng & Insight đối thủ (Markdown):
                - 03 Viral Trends nổi bật trên MXH.
                - Đánh giá chiến dịch của đối thủ và gaps nội dung.
                - Danh sách dẫn nguồn (URL) từ Internet.
            """),
            agent=agent,
        )

    def content_creation_task(self, agent, research_task: Task):
        """Bước 2: Sáng tạo Nội dung Viral (Social Media Content Creation)."""
        return Task(
            description=dedent("""
                Dựa trên dữ liệu thị trường và cảm xúc khách hàng, hãy đóng vai một Creative Director.
                
                QUY TRÌNH:
                1. Đọc văn phong từ marketing_content để giữ đúng 'giọng điệu' thương hiệu.
                2. Truy vấn 'social_sentiment' để nắm bắt cảm xúc của khách hàng.
                3. Phải tạo ra 03 mẫu bài đăng Facebook/Instagram/TikTok khác nhau:
                   - Mẫu 1 (Viral/Hài hước): Bắt trend từ dữ liệu social_sentiment hoặc trends tìm được.
                   - Mẫu 2 (Kỹ thuật/Expert): Dùng thông số thực từ competitor_products để so sánh khéo léo.
                   - Mẫu 3 (Kêu gọi hành động/Sales): Dựa trên ROI và khuyến mãi đối thủ để đưa ra ưu đãi không thể từ chối.

                YÊU CẦU ĐẦU RA CHO MỖI MẪU BÀI ĐĂNG:
                - Tiêu đề (Hook) hấp dẫn.
                - Nội dung chính (Body) dễ đọc, tự nhiên.
                - Danh sách Hashtag.
                - Gợi ý hình ảnh/video mô tả cụ thể bên dưới mỗi post.
            """),
            expected_output=dedent("""
                Danh sách 03 bài đăng MXH hoàn chỉnh (Facebook, Instagram, TikTok Script):
                - Tiêu đề, Body, Hashtags.
                - Gợi ý thiết kế hình ảnh/video đi kèm chuẩn xác.
            """),
            agent=agent,
            context=[research_task],
        )

    def marketing_strategy_task(self, agent, research_task: Task, content_task: Task, tools: List[BaseTool]):
        """Bước 3: Kế hoạch Hành động Tuần - Gợi ý Chiến lược Tăng trưởng."""
        return Task(
            description=dedent("""
                Tổng hợp "Cố vấn Kế hoạch Hành động Tuần" dành cho Team Marketing.
                Biến các con số khô khan thành Insight hành động. Đừng chỉ nói doanh thu tăng, hãy nói: 'Nhóm Gen Z đang chuộng trả góp cho iPhone màu Titan, hãy đẩy mạnh bài viết về chính sách tài chính vào khung giờ 20h-22h'.

                QUY TRÌNH BAO GỒM:
                1. Sử dụng 'Data Triangulation': Lấy dữ liệu bán hàng (sales_performance) và dữ liệu chiến dịch (marketing_campaigns) làm căn cứ (Evidence) để lên kế hoạch.
                2. Định vị rõ các yếu tố chiến lược dựa trên dữ liệu và bài đăng đã tạo.
                3. Trình bày định dạng Markdown với các `Hộp gợi ý` (Alert boxes / Blockquotes) để làm nổi bật trọng tâm.

                CẤU TRÚC BÁO CÁO PHẢI CÓ:
                - # 🚀 KẾ HOẠCH HÀNH ĐỘNG TUẦN & POST SUGGESTIONS
                - ## 🎯 Đối tượng Mục tiêu & Kênh Ưu tiên
                - ## 💡 Thông điệp Chủ đạo (Key Message)
                - ## 📝 Gợi ý Bài đăng (Copy paste nguyên văn 3 bài đăng từ Content Strategist vào đây để tiện sử dụng)
                - ## ⚠️ Cảnh báo & Đề xuất (Dựa trên con số thực từ database để đề xuất ưu đãi bù đắp).
            """),
            expected_output=dedent("""
                Một Kế hoạch Hành động Tuần Markdown chuyên nghiệp:
                - Gồm Đối tượng, Kênh, Thông điệp chủ đạo.
                - Trình bày 03 bài đăng MXH rõ ràng, có thể copy-paste.
                - Các 'Hộp gợi ý' hành động sắc bén từ số liệu SQL (Ví dụ: Dựa trên 40% doanh thu là sản phẩm X...).
            """),
            agent=agent,
            context=[research_task, content_task],
            tools=tools,
        )
