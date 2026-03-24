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
            # dedent giúp viết mô tả dài mà không bị lỗi thụt lề
            description=dedent(f""" 
                Tìm kiếm và phân tích 5 tin tức quan trọng nhất về chủ đề: {market_topic}.
                Tập trung vào các chiến dịch mới, sản phẩm công nghệ hoặc xu hướng tiêu dùng 
                của các ông lớn smartphone (Samsung, Apple, Xiaomi) trong 24 giờ qua.
            """),
            expected_output="Một bản tóm tắt danh sách 5 tin tức hot nhất kèm link nguồn và phân tích nhanh tầm ảnh hưởng.",
            agent=agent
        )

    def content_creation_task(self, agent):
        if Task is None:
            return None
            
        return Task(
            description=dedent("""
                Dựa trên báo cáo nghiên cứu thị trường công nghệ vừa nhận được, hãy sáng tạo:
                1. Trước tiên, truy vấn database để lấy dữ liệu sentiment:
                   SQL: SELECT keyword, positive_score, top_complaint, trending_platform FROM social_sentiment ORDER BY positive_score DESC
                   (Lưu ý: bảng social_sentiment CÓ cột positive_score, negative_score, keyword, top_complaint, trending_platform. KHÔNG có cột 'sentiment' hay 'topic')
                2. Ba (3) mẫu caption Facebook hấp dẫn tập trung vào hiệu năng, trải nghiệm người dùng và tính năng AI (bao gồm Emoji và Hashtag #TechSavvy).
                3. Một (1) ý tưởng tổ chức mini-game hoặc sự kiện tại cửa hàng để thu hút khách hàng công nghệ.
                Yêu cầu: Ngôn ngữ hiện đại, tech-savvy, phù hợp với thương hiệu công nghệ cao cấp.
            """),
            expected_output="Bản thảo nội dung Marketing chi tiết gồm caption và ý tưởng sự kiện công nghệ.",
            agent=agent
        )

    def analytics_report_task(self, agent):
        if Task is None:
            return None
        return Task(
            description=dedent(f"""
                Thực hiện phân tích sâu và viết Báo cáo Chiến lược Marketing cho thị trường smartphone 2026.
                Báo cáo PHẢI được viết dưới định dạng MARKDOWN và tuân thủ cấu trúc chuyên nghiệp.
                
                QUAN TRỌNG NHẤT: Bạn PHẢI dùng tool "query_marketing_db" để lấy TOÀN BỘ dữ liệu cần thiết. 
                TUYỆT ĐỐI KHÔNG được bịa đặt Specs hay số liệu không có trong Database.

                CẤU TRÚC BÁO CÁO BẮT BUỘC:

                I. TÓM TẮT CHO LÃNH ĐẠO (EXECUTIVE SUMMARY)
                   - Viết 3-4 câu tóm tắt những phát hiện quan trọng nhất và các đề xuất chính.

                II. PHÂN TÍCH THỊ TRƯỜNG & HIỆU SUẤT KINH DOANH
                   - Truy vấn và phân tích dữ liệu từ bảng 'sales' và 'sales_performance'.
                   - Trình bày tổng doanh thu, sản lượng bán ra.
                   - Tạo bảng xếp hạng các sản phẩm bán chạy nhất (Top Sellers).

                III. TÌNH BÁO CẠNH TRANH (COMPETITIVE INTELLIGENCE)
                   - Truy vấn bảng 'competitor_products' để lấy thông tin đối thủ (Apple, Samsung, Xiaomi).
                   - Lập bảng so sánh chi tiết: key_features, giá (price), điểm mạnh (strengths), điểm yếu (weaknesses).
                   - Đưa ra nhận định ngắn gọn về vị thế cạnh tranh.

                IV. PHÂN TÍCH KHÁCH HÀNG & THỊ TRƯỜNG (CUSTOMER & MARKET INSIGHTS)
                   - Truy vấn bảng 'social_sentiment'.
                   - Phân tích chỉ số cảm xúc (positive_score).
                   - Trích dẫn những lời phàn nàn hàng đầu (top_complaint) và các xu hướng thảo luận trên (trending_platform).

                V. HIỆU QUẢ CHIẾN DỊCH MARKETING
                   - Truy vấn bảng 'marketing_campaigns'.
                   - Phân tích Tỷ lệ chuyển đổi (conversion_rate) và ROI.
                   - Đánh giá hiệu suất của các kênh marketing.

                VI. PHÂN TÍCH SWOT & ĐỀ XUẤT CHIẾN LƯỢC
                   - Dựa trên TOÀN BỘ dữ liệu đã phân tích ở trên, xây dựng mô hình SWOT:
                     - Strengths (Điểm mạnh): Lợi thế nội tại của sản phẩm/công ty.
                     - Weaknesses (Điểm yếu): Những yếu kém nội tại cần khắc phục.
                     - Opportunities (Cơ hội): Các yếu tố bên ngoài có thể tận dụng (xu hướng thị trường, công nghệ mới).
                     - Threats (Thách thức): Các yếu tố bên ngoài có thể gây hại (đối thủ, thay đổi chính sách).
                   - Dựa vào SWOT, đưa ra ít nhất 3 ĐỀ XUẤT CHIẾN LƯỢC rõ ràng, có tính hành động cao (ví dụ: "Tập trung R&D cải thiện điểm yếu [Tên điểm yếu] để cạnh tranh với [Tên đối thủ]").

                VII. XUẤT BẢN (QUAN TRỌNG)
                   - Sau khi hoàn tất nội dung báo cáo Markdown, bạn PHẢI gọi tool 'publish_to_google_docs' để đẩy báo cáo lên Google Drive với:
                     - title: "Comprehensive Smartphone Market Strategic Report 2026"
                     - content: [Toàn bộ nội dung báo cáo Markdown bạn vừa viết]
                
                Nhiệm vụ chỉ được coi là hoàn thành khi báo cáo được xuất bản thành công.
            """),
            expected_output="Bản báo cáo Markdown đầy đủ số liệu thực từ DB ĐÃ ĐƯỢC XUẤT BẢN thành công lên Google Docs (kèm URL xác nhận).",
            agent=agent
        )