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
                Thực hiện phân tích thị trường smartphone 2026. 
                QUAN TRỌNG NHẤT: Bạn PHẢI dùng tool "query_marketing_db" để lấy dữ liệu. 
                TUYỆT ĐỐI KHÔNG được bịa đặt Specs hay số liệu không có trong Database.

                CÁC BƯỚC BẮT BUỘC:
                1. Truy vấn bảng 'sales' và 'sales_performance' để lấy doanh số thật.
                2. Truy vấn bảng 'competitor_products'. Chú ý dùng đúng 'key_features', 'strengths', 'weaknesses' từ DB.
                3. Truy vấn bảng 'social_sentiment' và 'marketing_campaigns'.
                
                4. Viết BÁO CÁO MARKDOWN:
                   - Phải có các bảng so sánh số liệu rõ ràng.
                   - Phải trích dẫn đúng các lỗi (top_complaint) từ DB.
                
                5. XUẤT BẢN (QUAN TRỌNG): 
                   Sau khi viết xong nội dung, bạn PHẢI gọi tool 'publish_to_google_docs' 
                   để đẩy báo cáo lên Google Drive với:
                   - title: "Smartphone Market Strategic Report 2026"
                   - content: [Toàn bộ nội dung báo cáo Markdown bạn vừa viết]
                
                Nếu không gọi tool xuất bản ở bước cuối, nhiệm vụ coi như thất bại.
            """),
            expected_output="Bản báo cáo Markdown đầy đủ số liệu thực từ DB ĐÃ ĐƯỢC XUẤT BẢN thành công lên Google Docs (kèm URL xác nhận).",
            agent=agent
        )