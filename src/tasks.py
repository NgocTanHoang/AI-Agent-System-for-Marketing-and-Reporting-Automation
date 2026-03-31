"""
MarketingTasks — Pipeline 4 stages theo chuẩn Executive Strategic Reporting.
Quy trình được thiết kế nhằm mang lại các nhận định (Insights) mang tầm vóc chiến lược.
"""
from typing import List
from textwrap import dedent

try:
    from crewai import Task
    from crewai.tools import BaseTool
except ImportError as e:
    raise ImportError(f"Không thể import CrewAI: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# GROUND TRUTH — Dữ liệu cứng từ database, dùng làm anchor cho các prompt.
# Đảm bảo tính nhất quán dữ liệu (Data Integrity).
# ─────────────────────────────────────────────────────────────────────────────
_REGIONS = "North, South, Central, Highlands"
_ROI_DATA = "TikTok=1383.21 (budget 235tr), Instagram=995.0 (budget 28tr), Facebook=980.42 (budget 166tr), KOL=951.66, YouTube=333.57 (budget 461tr), Google Search=332.98 (budget 468tr)"
_REGION_NOTE = f"⚠️ CHỈ DÙNG 4 KHU VỰC NÀY: {_REGIONS}."


class MarketingTasks:

    # ══════════════════════════════════════════════════════════════════════════
    # STAGE 1 — TÌNH BÁO THỊ TRƯỜNG & BENCHMARKING ĐỐI THỦ
    # ══════════════════════════════════════════════════════════════════════════

    def research_task(self, agent, market_topic: str) -> Task:
        return Task(
            description=dedent(f"""
                NHIỆM VỤ: Intelligence Intelligence — Phân tích {market_topic}
                
                {_REGION_NOTE}

                BƯỚC 1 — BENCHMARKING ĐỐI THỦ (Bắt buộc SQL, ≥ 3 đối thủ):
                    SELECT brand, model_name, key_features, current_price,
                           strengths, weaknesses
                    FROM competitor_products
                    ORDER BY current_price DESC
                    LIMIT 6

                Xuất bảng: | Đối Thủ | Model | Tính Năng Nổi Bật | Giá Niêm Yết (VNĐ) | Lợi Thế Cạnh Tranh | Gót Chân Achilles |
                Lưu ý định dạng tiền tệ: 32,000,000 VNĐ.

                BƯỚC 1.5 — MODEL DẪN ĐẦU DOANH THU (Bắt buộc SQL):
                    SELECT model_name, SUM(units_sold * unit_price) AS revenue
                    FROM sales
                    GROUP BY model_name
                    ORDER BY revenue DESC
                    LIMIT 1

                BƯỚC 2 — PHÂN TÍCH ƯU THẾ & RỦI RO (Dựa trên dữ liệu SQL):
                - ✅ Lợi thế cạnh tranh vượt trội: Nêu rõ thông số và ưu thế so với đối thủ trực tiếp.
                - ❌ Thách thức cạnh tranh hiện hữu: Phân tích khách quan các điểm chưa tối ưu.

                BƯỚC 3 — PHÂN TÍCH ĐƠN VỊ ĐÃI NGỘ THẤP (Bắt buộc SQL):
                    SELECT model_name, region, SUM(units_sold) AS total_units,
                           ROUND(AVG(unit_price), 0) AS avg_price
                    FROM sales
                    GROUP BY model_name, region
                    ORDER BY total_units ASC
                    LIMIT 2

                BƯỚC 4 — PHẢN HỒI THỊ TRƯỜNG — Social Sentiment (Bắt buộc SQL):
                    SELECT keyword, top_complaint, negative_score,
                           total_mentions, trending_platform
                    FROM social_sentiment
                    ORDER BY negative_score DESC
                    LIMIT 3

                BƯỚC 5 — PHÂN TÍCH XU HƯỚNG NGƯỜI TIÊU DÙNG:
                Sử dụng công cụ tìm kiếm để xác định 3 xu hướng (Trend) đang định hình thị trường smartphone tại Việt Nam.

                ⚠️ QUY TẮC SQL & ĐỊNH DẠNG:
                - Model: model_name | Giá: unit_price hoặc current_price.
                - Định dạng số: Luôn có dấu phẩy phân cách (ví dụ: 12,500,000 VNĐ).
                - Khu vực: Tuyệt đối chỉ dùng {_REGIONS}.
            """),
            expected_output=dedent("""
                ## 🛡️ I. Bảng Benchmarking Đối Thủ (Competitive Mapping)
                | Đối Thủ | Model | Tính Năng Nổi Bật | Giá Niêm Yết (VNĐ) | Lợi Thế Cạnh Tranh | Gót Chân Achilles |
                (Dữ liệu thực tế, định dạng 32,000,000 VNĐ)

                ## 📈 II. Phân Tích Hiệu Suất Sản Phẩm Dẫn Đầu (Market Leader)
                *Model: [model_name] | Tổng Doanh Thu: [revenue] VNĐ*

                ## ⚔️ III. Đánh Giá Vị Thế Cạnh Tranh
                - ✅ Ưu Thế Vượt Trội: [Mô tả lợi thế + dữ liệu đối chiếu]
                - ❌ Thách Thức Hiện Hữu: [Phân tích rủi ro/điểm yếu từ dữ liệu]

                ## 📉 IV. Danh Mục Sản Phẩm Đang Cần Cải Thiện
                | model_name | region | total_units | avg_price |
                (Dữ liệu thực tế từ hệ thống)

                ## 💎 V. Insight Từ Phản Hồi Khách Hàng (Social Listening)
                | keyword | top_complaint | negative_score | trending_platform |

                ## 🚀 VI. Xu Hướng Thị Trường Key Insights
            """),
            agent=agent,
        )

    # ══════════════════════════════════════════════════════════════════════════
    # STAGE 2 — SÁNG TẠO NỘI DUNG ĐỊNH VỊ THƯƠNG HIỆU (AIDA EXECUTIVE)
    # ══════════════════════════════════════════════════════════════════════════

    def content_creation_task(self, agent, research_task: Task) -> Task:
        return Task(
            description=dedent("""
                NHIỆM VỤ: Brand Strategist — Xây dựng 03 phương án nội dung định vị thương hiệu đẳng cấp.
                
                YÊU CẦU:
                - Đọc context từ Intelligence Lead để xác định: top_complaint, điểm yếu đối thủ, và model hiệu suất thấp.
                - Sử dụng ngôn ngữ Executive Marketing chuyên nghiệp, tinh tế, giàu giá trị.
                - Định dạng chuẩn AIDA Professional.

                MẪU 1 — 🛡️ GIẢI PHÁP CHIẾN LƯỢC (Pain Point Optimization)
                - [HOOK]: Đánh vào nhu cầu thực tế và trải nghiệm xứng tầm (Ví dụ: "Nâng tầm hiệu suất công việc với công nghệ sạc nhanh dẫn đầu thị trường").
                - [BODY]: Khẳng định ưu thế qua thông số kỹ thuật vượt trội (Camera, Chipset, dung lượng Pin). So sánh tinh tế với các hạn chế của đối thủ cạnh tranh.
                - [DESIRE]: Khắc họa giá trị thăng dư và sự hài lòng bền vững khi sở hữu sản phẩm.
                - [CTA]: Lời mời gọi hành động chuyên nghiệp (Ví dụ: "Khám phá đặc quyền tại hệ thống cửa hàng").

                MẪU 2 — 💎 KHẲNG ĐỊNH VỊ THẾ (Flexing Premium)
                - Tập trung vào Model Dẫn Đầu Doanh Thu. Nêu bật sự đẳng cấp và uy tín thương hiệu đã được thị trường công nhận.
                - Nêu rõ đặc quyền sở hữu và trải nghiệm "Đỉnh cao công nghệ".
                - CTA: "Liên hệ tư vấn giải pháp sở hữu ngay hôm nay".

                MẪU 3 — 📈 TỐI ƯU HÓA CƠ HỘI (Strategic Deal)
                - Dành cho model đang cần cải thiện KPI. 
                - Hook: Nhấn mạnh vào giá trị đầu tư tối ưu cho một sản phẩm cao cấp. 
                - Desire: Số lượng hữu hạn dành riêng cho nhóm khách hàng ưu tú.
                - CTA: Lời mời trải nghiệm ngay lập tức để nhận ưu đãi đặc quyền.

                ⚠️ QUY TẮC NGÔN NGỮ & ĐỊNH DẠNG:
                1. 100% tiếng Việt có dấu, đúng ngữ pháp và dấu câu.
                2. Sử dụng Emoji tinh tế (📈, 💎, 🛡️, 🤝).
                3. Tiền tệ chuẩn: 16,860,000,000 VNĐ.
                4. Từ ngữ: Chuyên nghiệp, lịch sự, không sử dụng biệt ngữ tiêu cực hoặc từ ngữ dân dã.
            """),
            expected_output=dedent("""
                ## 🛡️ PHƯƠNG ÁN 1 — GIẢI PHÁP CHIẾN LƯỢC
                **[HOOK]**: ...
                **[BODY]**: ...
                **[DESIRE]**: ...
                **[CTA]**: ...
                **[HASHTAGS]**: (10 hashtags chuyên nghiệp)

                ---
                ## 💎 PHƯƠNG ÁN 2 — KHẲNG ĐỊNH VỊ THẾ
                **[HOOK]**: ...
                ...

                ---
                ## 📈 PHƯƠNG ÁN 3 — TỐI ƯU HÓA CƠ HỘI
                **[HOOK]**: ...
                ...
            """),
            agent=agent,
            context=[research_task],
        )

    # ══════════════════════════════════════════════════════════════════════════
    # STAGE 2.5 — PRE-FETCH SQL TÀI CHÍNH
    # ══════════════════════════════════════════════════════════════════════════

    def data_fetch_task(self, agent, research_task: Task, content_task: Task) -> Task:
        return Task(
            description=dedent(f"""
                NHIỆM VỤ: Truy xuất dữ liệu tài chính phục vụ báo cáo cấp quản trị.
                Chỉ trả về 3 bảng Markdown chứa kết quả thô từ SQL, không kèm phân tích.

                {_REGION_NOTE}

                SQL 1 — Chỉ số ROI & CPA theo kênh (TikTok, Instagram, Facebook, YouTube, Google Search, KOL).
                SQL 2 — Doanh thu phân bổ theo Danh mục Sản phẩm (Sắp xếp giảm dần).
                SQL 3 — Doanh thu phân bổ theo Khu vực Địa lý ({_REGIONS}).
            """),
            expected_output="3 bảng Markdown dữ liệu tài chính thô.",
            agent=agent,
            context=[research_task, content_task],
        )

    # ══════════════════════════════════════════════════════════════════════════
    # STAGE 3 — BÁO CÁO CHIẾN LƯỢC EXECUTIVE EXCELLENCE
    # ══════════════════════════════════════════════════════════════════════════

    def marketing_strategy_task(
        self, agent, research_task: Task, content_task: Task,
        data_fetch_task: Task, tools: List[BaseTool]
    ) -> Task:
        return Task(
            description=dedent(f"""
                NHIỆM VỤ: Hoàn thiện BÁO CÁO CHIẾN LƯỢC EXECUTIVE EXCELLENCE.
                Bạn là Chief Strategy Officer (CSO). Báo cáo của bạn phải thể hiện tầm vóc lãnh đạo và tư duy quản trị dựa trên dữ liệu.

                {_REGION_NOTE}

                CẤU TRÚC BÁO CÁO — 7 PHẦN CHIẾN LƯỢC:

                ## 🔭 I. Tổng Quan Chiến Lược & Phân Tích Đa Chiều (Data Triangulation)
                Nhận định mang tính định hướng cấp cao. Sử dụng các cụm từ: "Khai thác dư địa tăng trưởng", "Tận dụng hiệu ứng quy mô", "Xác lập lợi thế dẫn đầu".
                Đặt và trả lời 3 câu hỏi chiến lược dựa trên dữ liệu thực tế từ context.

                ## 📊 II. Phân Tích Hiệu Quả Tài Chính & Tối Ưu Hóa Nguồn Lực
                Trình bày bảng ROI/CPA. Thực hiện phân tích đúng chiều:
                - ROI CAO + Ngân sách THẤP → "Kênh đang bị giới hạn tiềm năng — Đề xuất Tăng cường nguồn lực ưu tiên".
                - ROI THẤP + Ngân sách CAO → "Hiệu suất đầu tư chưa tương xứng — Đề xuất Tái phân bổ ngân sách tập trung".

                ## 🏆 III. Toàn Cảnh Doanh Thu & Định Vị Sản Phẩm
                Bảng doanh thu chi tiết (định dạng 48,000,000,000 VNĐ).
                Sử dụng các thuật ngữ: "Sản phẩm Key Driver", "Dòng sản phẩm Chiến lược", "Khu vực trọng điểm".

                ## ⚔️ IV. Cạnh Tranh Chiến Lược & Benchmark Đối Đầu
                Xác lập các điểm "Thắng - Thua" dựa trên dữ liệu benchmarking. Đề xuất phương án tối ưu hóa lợi thế cạnh tranh để chiếm lĩnh thị phần.

                ## 📱 V. Chiến Lược Nội Dung Truyền Thông Xứng Tầm
                Trình bày nguyên văn 03 phương án nội dung AIDA Executive từ Brand Strategist. Đảm bảo ngôn ngữ tinh tế và truyền cảm hứng.

                ## 🗺️ VI. Lộ Trình Triển Khai 7 Ngày (Implementation Roadmap)
                Xây dựng bảng kế hoạch cụ thể cho 7 ngày tới. 
                - Thay "Mật lệnh" bằng "Hành động Chiến lược". 
                - Ngân sách: Format 50,000,000 VNĐ.
                - Khu vực: Chỉ sử dụng {_REGIONS}.

                ## ⚠️ VII. Quản Trị Rủi Ro & Điểm Kiểm Soát (Risk Management)
                Xác định ít nhất 3 rủi ro chiến lược và các biện pháp giảm thiểu.
                Format: "⚠️ Rủi ro: ... → 📡 Dấu hiệu nhận biết: ... → 🛡️ Phương án xử lý: ..."

                ⚠️ YÊU CẦU QUY CHUẨN:
                - Tiếng Việt 100% chuẩn mực văn phòng cấp cao.
                - Tuyệt đối không sử dụng slang, từ ngữ dân dã hoặc các biểu cảm tiêu cực.
                - Toàn bộ báo cáo ≥ 1000 từ để đạt độ sâu sắc cần thiết.
            """),
            expected_output=dedent(f"""
                BÁO CÁO CHIẾN LƯỢC EXECUTIVE EXCELLENCE:

                ## 🔭 I. Tổng Quan Chiến Lược & Phân Tích Đa Chiều
                ## 📊 II. Phân Tích Hiệu Quả Tài Chính & Tối Ưu Hóa Nguồn Lực
                ## 🏆 III. Toàn Cảnh Doanh Thu & Định Vị Sản Phẩm
                ## ⚔️ IV. Cạnh Tranh Chiến Lược & Benchmark Đối Đầu
                ## 📱 V. Chiến Lược Nội Dung Truyền Thông Xứng Tầm
                ## 🗺️ VI. Lộ Trình Triển Khai 7 Ngày (Implementation Roadmap)
                ## ⚠️ VII. Quản Trị Rủi Ro & Điểm Kiểm Soát (Risk Management)
            """),
            agent=agent,
            context=[research_task, content_task, data_fetch_task],
            tools=tools,
        )
