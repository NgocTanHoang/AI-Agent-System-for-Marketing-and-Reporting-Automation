content = r"""try:
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
            description=dedent(f\"\"\" 
                Tìm kiếm và phân tích 5 tin tức quan trọng nhất về chủ đề: {market_topic}.
                Tập trung vào các chiến dịch mới, sản phẩm công nghệ hoặc xu hướng tiêu dùng 
                của các ông lớn smartphone (Samsung, Apple, Xiaomi) trong 24 giờ qua.
            \"\"\" ),
            expected_output="Một bản tóm tắt danh sách 5 tin tức hot nhất kèm link nguồn và phân tích nhanh tầm ảnh hưởng.",
            agent=agent
        )

    def content_creation_task(self, agent):
        if Task is None:
            return None
            
        return Task(
            description=dedent(\"\"\"
                Dựa trên báo cáo nghiên cứu thị trường công nghệ vừa nhận được, hãy sáng tạo:
                1. Trước tiên, truy vấn database để lấy dữ liệu sentiment:
                   SQL: SELECT keyword, positive_score, top_complaint, trending_platform FROM social_sentiment ORDER BY positive_score DESC
                   (Lưu ý: bảng social_sentiment CÓ cột positive_score, negative_score, keyword, top_complaint, trending_platform. KHÔNG có cột 'sentiment' hay 'topic')
                2. Ba (3) mẫu caption Facebook hấp dẫn tập trung vào hiệu năng, trải nghiệm người dùng và tính năng AI (bao gồm Emoji và Hashtag #TechSavvy).
                3. Một (1) ý tưởng tổ chức mini-game hoặc sự kiện tại cửa hàng để thu hút khách hàng công nghệ.
                Yêu cầu: Ngôn ngữ hiện đại, tech-savvy, phù hợp với thương hiệu công nghệ cao cấp.
            \"\"\" ),
            expected_output="Bản thảo nội dung Marketing chi tiết gồm caption và ý tưởng sự kiện công nghệ.",
            agent=agent
        )

    def analytics_report_task(self, agent):
        if Task is None:
            return None
        return Task(
            description=dedent(f\"\"\"
                Thực hiện phân tích sâu và viết Báo cáo Chiến lược Marketing cho thị trường smartphone 2026.
                Báo cáo PHẢI được viết dưới định dạng MARKDOWN và tuân thủ cấu trúc \"Executive Report\" chuyên nghiệp.
                
                QUAN TRỌNG NHẤT: Bạn PHẢI dùng tool \"query_marketing_db\" để lấy TOÀN BỘ dữ liệu. 
                TUYỆT ĐỐI KHÔNG được bịa đặt số liệu.

                YÊU CẦU ĐỊNH DẠNG & BIỆN LUẬN:
                1. Tiền tệ: Luôn định dạng số tiền sang VNĐ (Ví dụ: 625 tỷ VNĐ) thay vì số thập phân thô.
                2. So sánh: Phải tính toán % tăng trưởng hoặc tỷ trọng (Ví dụ: 'iPhone chiếm 48% tổng doanh số').
                3. Insight: Phải biện luận từ số liệu. Ví dụ: Từ sentiment 0.8, viết thành 'Thị trường phản hồi rất tích cực (80%) với tính năng màn hình gập'.
                4. Trực quan hóa: Truy vấn SQL lấy (model_name, units_sold) ở dạng JSON, dùng \"create_sales_chart\" để vẽ biểu đồ và chèn ảnh vào báo cáo.

                CẤU TRÚC BÁO CÁO:
                I. TÓM TẮT CHO LÃNH ĐẠO (EXECUTIVE SUMMARY)
                   - Tóm tắt những phát hiện quan trọng nhất và 3 đề xuất chiến lược chính.
                II. PHÂN TÍCH DOANH SỐ & BIỂU ĐỒ TRỰC QUAN
                   - Trình bày bảng doanh số; chèn ảnh biểu đồ bằng cú pháp Markdown ![Chart](đường_dẫn_ảnh).
                III. TÌNH BÁO CẠNH TRANH (COMPETITIVE INTELLIGENCE)
                   - Lập bảng so sánh đối thủ (features, giá VNĐ, SWOT).
                IV. PHÂN TÍCH SENTIMENT & ROI
                   - Biện luận về hiệu quả chiến dịch và phản hồi khách hàng.
                V. KẾT LUẬN & ĐỀ XUẤT CHIẾN LƯỢC (3 đề xuất cụ thể).
                VI. XUẤT BẢN: Cuối cùng, gọi 'publish_to_google_docs' sau khi hoàn thành toàn bộ nội dung markdown.
            \"\"\" ),
            expected_output="Bản báo cáo Markdown 'Executive Report' đầy đủ số liệu thực, biểu đồ trực quan, và ĐÃ ĐƯỢC XUẤT BẢN thành công lên Google Docs.",
            agent=agent
        )
\"\"\"

with open('D:/cv/project/01_AI Agent System for Marketing and Reporting Automation/src/tasks.py', 'w', encoding='utf-8') as f:
    f.write(content)
