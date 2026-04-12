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
    # STAGE 1.5 — CREATIVE DECISION LAYER (Tầng Ra quyết định Sáng tạo)
    # ══════════════════════════════════════════════════════════════════════════

    def creative_decision_task(self, agent, research_task: Task) -> Task:
        """Decision Layer: Chuyển hóa dữ liệu thô thành Creative Brief chuẩn xác."""
        return Task(
            description=dedent(f"""
                NHIỆM VỤ: Creative Director — Phân tích kết quả nghiên cứu và ra quyết định định hướng sáng tạo.

                Bạn KHÔNG viết nội dung marketing. Bạn CHỈ ra quyết định chiến lược sáng tạo.
                Đọc kỹ toàn bộ output từ Intelligence Lead (research_task) và xây dựng một CREATIVE BRIEF
                có cấu trúc chặt chẽ để định hướng cho Brand Strategist thực thi.

                {_REGION_NOTE}

                PHÂN TÍCH BẮT BUỘC:

                A. DATA INSIGHT EXTRACTION (Rút trích Insight từ dữ liệu):
                   - Xác định Top 1 model dẫn đầu doanh thu và lý do (từ context).
                   - Xác định Top 1 model hiệu suất thấp nhất và nguyên nhân (từ context).
                   - Xác định Top 1 complaint nghiêm trọng nhất từ Social Sentiment (từ context).
                   - Xác định 1-2 điểm yếu nổi bật nhất của đối thủ (từ benchmarking context).

                B. STRATEGIC CREATIVE DECISIONS:
                   1. GIỌNG ĐIỆU (Tone of Voice): Chọn 1 trong các hướng sau và giải thích lý do dựa trên dữ liệu:
                      - "Confident Premium" (Tự tin đẳng cấp) — Phù hợp khi sản phẩm dẫn đầu doanh thu.
                      - "Empathetic Problem-Solver" (Thấu hiểu - Giải pháp) — Phù hợp khi có pain point rõ ràng.
                      - "Bold Challenger" (Thách thức táo bạo) — Phù hợp khi đối thủ có điểm yếu để khai thác.

                   2. GÓC TIẾP CẬN (Content Angles) — Chọn 3 góc, mỗi góc phải có cơ sở dữ liệu:
                      - Góc 1: Dựa trên ưu thế kỹ thuật vượt trội so với đối thủ.
                      - Góc 2: Dựa trên pain point / top complaint từ Social Listening.
                      - Góc 3: Dựa trên cơ hội thị trường (model cần cải thiện KPI).

                   3. ĐỐI TƯỢNG MỤC TIÊU (Target Personas) — Xác định 2 personas ưu tiên:
                      - Mô tả: Tên persona, độ tuổi, hành vi mua hàng, kênh tiếp cận ưu tiên.
                      - Cơ sở: Dựa trên dữ liệu customer_age_group và payment_method từ context.

                   4. THÔNG ĐIỆP CHỦ ĐẠO (Key Messages) — Chính xác 3 thông điệp:
                      - Message gắn với Model dẫn đầu (Flexing).
                      - Message gắn với Pain Point (Solution).
                      - Message gắn với Model cần cải thiện (Opportunity).

                   5. KÊNH TRUYỀN THÔNG ƯU TIÊN:
                      - Dựa trên dữ liệu ROI có sẵn: {_ROI_DATA}
                      - Xếp hạng 3 kênh ưu tiên để phân bổ nội dung, kèm lý do.

                ⚠️ QUY TẮC:
                - Mọi quyết định PHẢI trích dẫn số liệu cụ thể từ context.
                - KHÔNG viết nội dung marketing, KHÔNG viết post, KHÔNG viết caption.
                - Đầu ra là một Creative Brief dạng bảng có cấu trúc rõ ràng.
            """),
            expected_output=dedent("""
                # 🎯 CREATIVE BRIEF — CHIẾN LƯỢC ĐỊNH HƯỚNG SÁNG TẠO

                ## A. DATA INSIGHTS DASHBOARD
                | Chỉ số | Giá trị | Nguồn |
                |---|---|---|
                | Model dẫn đầu doanh thu | [model_name] — [revenue] VNĐ | SQL: sales |
                | Model hiệu suất thấp | [model_name] — [units] units | SQL: sales |
                | Top complaint | [complaint] — Score: [score] | SQL: social_sentiment |
                | Điểm yếu đối thủ chiến lược | [brand] — [weakness] | SQL: competitor_products |

                ## B. QUYẾT ĐỊNH SÁNG TẠO

                ### 1. Giọng Điệu (Tone)
                **[Tone đã chọn]** — Lý do: [giải thích dựa trên dữ liệu]

                ### 2. Góc Tiếp Cận (Angles)
                | # | Góc | Cơ sở dữ liệu |
                |---|---|---|
                | 1 | [Angle 1] | [Data backing] |
                | 2 | [Angle 2] | [Data backing] |
                | 3 | [Angle 3] | [Data backing] |

                ### 3. Target Personas
                | Persona | Độ tuổi | Hành vi | Kênh ưu tiên |
                |---|---|---|---|
                | [Persona 1] | ... | ... | ... |
                | [Persona 2] | ... | ... | ... |

                ### 4. Key Messages
                - 💎 Flexing: [Message cho model dẫn đầu]
                - 🛡️ Solution: [Message cho pain point]
                - 📈 Opportunity: [Message cho model cần cải thiện]

                ### 5. Kênh Ưu Tiên
                | Hạng | Kênh | ROI | Lý do |
                |---|---|---|---|
            """),
            agent=agent,
            context=[research_task],
        )

    # ══════════════════════════════════════════════════════════════════════════
    # STAGE 2 — SÁNG TẠO NỘI DUNG ĐỊNH VỊ THƯƠNG HIỆU (AIDA EXECUTIVE)
    # ══════════════════════════════════════════════════════════════════════════

    def content_creation_task(self, agent, creative_decision_task: Task) -> Task:
        """Content execution giờ đây tuân theo Creative Brief, không tự diễn giải dữ liệu thô."""
        return Task(
            description=dedent("""
                NHIỆM VỤ: Brand Strategist — Xây dựng 03 phương án nội dung định vị thương hiệu đẳng cấp.

                ⚠️ QUAN TRỌNG: Bạn PHẢI tuân thủ 100% Creative Brief từ Creative Director.
                KHÔNG tự diễn giải dữ liệu thô. Mọi quyết định về giọng điệu, góc tiếp cận,
                đối tượng mục tiêu và thông điệp đã được Creative Director quyết định.
                Nhiệm vụ của bạn là THỰC THI xuất sắc các quyết định đó thành nội dung hoàn chỉnh.

                YÊU CẦU:
                - Đọc Creative Brief từ Creative Director để nắm: Tone, Angles, Personas, Key Messages.
                - Áp dụng đúng giọng điệu (Tone) đã được chỉ định.
                - Mỗi phương án nội dung phải gắn với 1 góc tiếp cận (Angle) từ Brief.
                - Sử dụng ngôn ngữ Executive Marketing chuyên nghiệp, tinh tế, giàu giá trị.
                - Định dạng chuẩn AIDA Professional.

                MẪU 1 — 🛡️ GIẢI PHÁP CHIẾN LƯỢC (Pain Point Optimization)
                - Góc tiếp cận: Angle từ Creative Brief liên quan đến Pain Point / Top Complaint.
                - [HOOK]: Đánh vào nhu cầu thực tế và trải nghiệm xứng tầm (Ví dụ: "Nâng tầm hiệu suất công việc với công nghệ sạc nhanh dẫn đầu thị trường").
                - [BODY]: Khẳng định ưu thế qua thông số kỹ thuật vượt trội (Camera, Chipset, dung lượng Pin). So sánh tinh tế với các hạn chế của đối thủ cạnh tranh.
                - [DESIRE]: Khắc họa giá trị thặng dư và sự hài lòng bền vững khi sở hữu sản phẩm.
                - [CTA]: Lời mời gọi hành động chuyên nghiệp (Ví dụ: "Khám phá đặc quyền tại hệ thống cửa hàng").
                - [CHANNEL]: Nêu rõ kênh ưu tiên từ Creative Brief và lý do.

                MẪU 2 — 💎 KHẲNG ĐỊNH VỊ THẾ (Flexing Premium)
                - Góc tiếp cận: Angle từ Creative Brief liên quan đến Model dẫn đầu doanh thu.
                - Tập trung vào Model Dẫn Đầu Doanh Thu. Nêu bật sự đẳng cấp và uy tín thương hiệu đã được thị trường công nhận.
                - Nêu rõ đặc quyền sở hữu và trải nghiệm "Đỉnh cao công nghệ".
                - CTA: "Liên hệ tư vấn giải pháp sở hữu ngay hôm nay".

                MẪU 3 — 📈 TỐI ƯU HÓA CƠ HỘI (Strategic Deal)
                - Góc tiếp cận: Angle từ Creative Brief liên quan đến Model cần cải thiện KPI.
                - Dành cho model đang cần cải thiện KPI.
                - Hook: Nhấn mạnh vào giá trị đầu tư tối ưu cho một sản phẩm cao cấp.
                - Desire: Số lượng hữu hạn dành riêng cho nhóm khách hàng ưu tú.
                - CTA: Lời mời trải nghiệm ngay lập tức để nhận ưu đãi đặc quyền.

                ⚠️ QUY TẮC NGÔN NGỮ & ĐỊNH DẠNG:
                1. 100% tiếng Việt có dấu, đúng ngữ pháp và dấu câu.
                   ⛔ CẤM ký tự Trung Quốc (面臨, 市場), Nhật, Hàn, hoặc tiếng Anh
                   (trừ thuật ngữ kỹ thuật: ROI, CPA, KPI, AIDA, CTR, KOL, Trade-in).
                2. Sử dụng Emoji tinh tế (📈, 💎, 🛡️, 🤝).
                3. Tiền tệ chuẩn: 16,860,000,000 VNĐ.
                4. Từ ngữ: Chuyên nghiệp, lịch sự, không sử dụng biệt ngữ tiêu cực hoặc từ ngữ dân dã.
                5. Mỗi MẪU phải ghi rõ: "Tuân theo Creative Brief — Góc: [tên góc], Tone: [tên tone]".
                6. ĐỘ SÂU BẮT BUỘC: Mỗi thành phần AIDA (Hook, Body, Desire, CTA) PHẢI là
                   1 đoạn văn đầy đủ gồm 3-4 câu chuyên nghiệp, có sức thuyết phục cao.
                   ⛔ CẤM viết 1 câu slogan ngắn rồi dừng lại.
            """),
            expected_output=dedent("""
                ## 🛡️ PHƯƠNG ÁN 1 — GIẢI PHÁP CHIẾN LƯỢC
                *Tuân theo Creative Brief — Góc: [Angle], Tone: [Tone]*

                **[HOOK]**: [Đoạn văn 3-4 câu. Mở đầu bằng câu hỏi khiêu khích hoặc số liệu gây sốc.
                Tiếp theo bằng mô tả pain point mà khách hàng đang gặp phải.
                Kết thúc bằng hint về giải pháp vượt trội mà sản phẩm mang lại.]

                **[BODY]**: [Đoạn văn 3-4 câu. Câu 1: Nêu thông số kỹ thuật cụ thể (chip, camera, pin).
                Câu 2: So sánh tinh tế với giới hạn của đối thủ (không nêu tên trực tiếp).
                Câu 3: Khẳng định ưu thế độc quyền. Câu 4: Dẫn chứng từ chuyên gia/giải thưởng.]

                **[DESIRE]**: [Đoạn văn 3-4 câu. Vẽ ra viễn cảnh cuộc sống/công việc khi sở hữu sản phẩm.
                Dùng ngôn ngữ cảm xúc đẳng cấp. Gợi mở về giá trị thặng dư lâu dài.
                Tạo cảm giác "không sở hữu = đang bỏ lỡ".]

                **[CTA]**: [2-3 câu hành động cụ thể. Kênh mua hàng + ưu đãi độc quyền + deadline.]
                **[CHANNEL]**: [Kênh ưu tiên + lý do dựa trên Creative Brief]
                **[HASHTAGS]**: (10 hashtags chuyên nghiệp)

                ---
                ## 💎 PHƯƠNG ÁN 2 — KHẲNG ĐỊNH VỊ THẾ
                *Tuân theo Creative Brief — Góc: [Angle], Tone: [Tone]*
                **[HOOK]**: [Đoạn văn 3-4 câu — tập trung vào model dẫn đầu doanh thu]
                **[BODY]**: [Đoạn văn 3-4 câu — đẳng cấp và uy tín được thị trường chứng minh]
                **[DESIRE]**: [Đoạn văn 3-4 câu — đặc quyền sở hữu, trải nghiệm đỉnh cao]
                **[CTA]**: [2-3 câu — tư vấn giải pháp sở hữu]

                ---
                ## 📈 PHƯƠNG ÁN 3 — TỐI ƯU HÓA CƠ HỘI
                *Tuân theo Creative Brief — Góc: [Angle], Tone: [Tone]*
                **[HOOK]**: [Đoạn văn 3-4 câu — giá trị đầu tư tối ưu]
                **[BODY]**: [Đoạn văn 3-4 câu — thông số vượt trội ở phân khúc]
                **[DESIRE]**: [Đoạn văn 3-4 câu — số lượng hữu hạn, cơ hội không lặp lại]
                **[CTA]**: [2-3 câu — trải nghiệm ngay + ưu đãi đặc quyền]
            """),
            agent=agent,
            context=[creative_decision_task],
        )

    # ══════════════════════════════════════════════════════════════════════════
    # STAGE 2.5 — PRE-FETCH SQL TÀI CHÍNH
    # ══════════════════════════════════════════════════════════════════════════

    def data_fetch_task(self, agent, research_task: Task, creative_decision_task: Task, content_task: Task) -> Task:
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
            context=[research_task, creative_decision_task, content_task],
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
                NHIỆM VỤ: Soạn thảo BÁO CÁO CHIẾN LƯỢC EXECUTIVE EXCELLENCE — Chuẩn McKinsey/BCG.
                Bạn là Chief Strategy Officer (CSO). Báo cáo này sẽ được trình lên CEO/CMO.
                Mỗi chữ bạn viết phải thể hiện tầm vóc lãnh đạo và năng lực tư duy quản trị vượt trội.

                {_REGION_NOTE}

                ⛔ QUY TẮC TUYỆT ĐỐI — VI PHẠM = BÁO CÁO BỊ TỪ CHỐI:
                1. CẤM đọc lại số liệu đã có trong bảng. Bảng cung cấp DATA — bạn cung cấp INSIGHT.
                2. CẤM bắt đầu câu bằng: "Dựa trên bảng này", "Như chúng ta thấy", "Từ dữ liệu trên",
                   "Bảng trên cho thấy", "Điều này có nghĩa là", "Chúng tôi có thể thấy rằng".
                3. CẤM phân tích đơn chiều (chỉ nói về 1 chỉ số riêng lẻ). Luôn phân tích GIAO CẮT:
                   ROI × Budget, Revenue × Market Share, Price × Sentiment.
                4. DƯỚI mỗi bảng dữ liệu: BẮT BUỘC viết ≥3 câu phân tích sâu theo framework:
                   - So What? (Ý nghĩa ẩn sau con số)
                   - Why So? (Nguyên nhân gốc rễ)
                   - Now What? (Hành động quyết liệt tiếp theo)
                5. Toàn bộ báo cáo ≥ 1500 từ. Mỗi phần ≥ 150 từ.

                🚨 HARD GUARDRAIL #6 — NGÔN NGỮ THUẦN KHIẾT:
                Output PHẢI 100% TIẾNG VIỆT. CẤM ký tự Trung Quốc (面臨, 市場, 競爭),
                Nhật (の, は), Hàn (는, 을). CẤM Tiếng Anh ngoài thuật ngữ kỹ thuật
                (ROI, CPA, KPI, BCG, AIDA, CTR, Trade-in, KOL).
                TRƯỚC KHI HOÀN THÀNH: Rà soát toàn bộ output — nếu có ký tự ngoại lai, XÓA ngay.

                🚨 HARD GUARDRAIL #7 — TÍNH TOÀN VẸN DỮ LIỆU:
                TUYỆT ĐỐI CẤM gom sản phẩm vào danh mục chung chung.
                CẤM viết: 'Điện tử', 'Thời trang', 'Hàng gia dụng', 'Electronics', 'Fashion'.
                BẮT BUỘC dùng CHÍNH XÁC tên model_name từ SQL (VD: 'Galaxy A56', 'iPhone 17 Pro',
                'Find X9 Pro', 'Pixel 10 Pro'). Nếu SQL trả về 'Galaxy S26 Ultra', bạn PHẢI viết
                'Galaxy S26 Ultra' — KHÔNG viết 'Samsung' hay 'Flagship'.

                🚨 HARD GUARDRAIL #8 — CẤM PHÂN TÍCH TAUTOLOGICAL:
                CẤM viết rủi ro thừa kiểu: 'Doanh thu giảm → Tăng nguồn lực'.
                CẤM viết phân tích lặp: 'Sản phẩm A có doanh thu cao → Sản phẩm A đóng góp nhiều'.
                PHẢI viết: Nguyên nhân gốc rễ + hành động cụ thể + số tiền + timeline.

                ═══════════════════════════════════════════════════
                CẤU TRÚC BÁO CÁO — 7 PHẦN CHIẾN LƯỢC
                ═══════════════════════════════════════════════════

                ## 🔭 I. Tổng Quan Chiến Lược & Phân Tích Đa Chiều (Executive Summary)
                Viết 1 đoạn mở đầu có sức nặng như một Partner McKinsey trình bày trước Board of Directors.
                - Câu 1: Khẳng định vị thế hiện tại (dựa trên số liệu doanh thu dẫn đầu).
                - Câu 2: Chỉ ra mâu thuẫn chiến lược lớn nhất (VD: "Kênh ROI cao nhất lại bị đầu tư thấp nhất").
                - Câu 3: Đề xuất Chủ đề Chiến lược (Strategic Theme) cho kỳ này.
                Sau đó đặt và trả lời 3 câu hỏi chiến lược. Mỗi câu trả lời phải có SỐ LIỆU CỤ THỂ:
                  Q1: "Đâu là động lực tăng trưởng chính (Growth Engine) và nó đang hoạt động ở mấy % công suất?"
                  Q2: "Khoảng trống cạnh tranh nào (Competitive Gap) chúng ta có thể khai thác ngay trong 7 ngày tới?"
                  Q3: "Rủi ro lớn nhất nào đang đe dọa vị thế dẫn đầu và phương án phòng thủ là gì?"

                ## 📊 II. Phân Tích Hiệu Quả Tài Chính & Tối Ưu Hóa Nguồn Lực
                Trình bày bảng ROI/CPA theo kênh. Dữ liệu tham chiếu: {_ROI_DATA}
                SAU BẢNG — Viết phân tích giao cắt (Intersection Analysis) bắt buộc:
                - Ma trận ROI × Budget: Phân loại mỗi kênh vào 1 trong 4 ô:
                  🌟 Star (ROI cao + Budget cao) → Duy trì và bảo vệ.
                  🚀 Rocket (ROI cao + Budget thấp) → ĐÂY LÀ CƠ HỘI LỚN NHẤT. Tăng gấp đôi ngân sách.
                  🐢 Turtle (ROI thấp + Budget cao) → Tái phân bổ khẩn cấp. Giảm ≥30% ngân sách.
                  ❓ Mystery (ROI thấp + Budget thấp) → Thí điểm hoặc loại bỏ.
                - Viết đề xuất hành động cụ thể: "Chuyển [X] tỷ VNĐ từ [Kênh A] sang [Kênh B]
                  vì mỗi đồng chi cho [Kênh B] tạo ra gấp [N] lần giá trị so với [Kênh A]."
                - KHÔNG được viết "TikTok có ROI cao nhất." Đó là đọc lại số.
                  PHẢI viết: "TikTok đang bị kìm hãm nghiêm trọng: ROI 1,383 (dẫn đầu) nhưng budget chỉ 235tr
                  (17% tổng chi). Mỗi đồng đầu tư vào TikTok tạo giá trị gấp 4.1 lần YouTube (ROI 333).
                  Đề xuất: Tái cấu trúc — chuyển 200tr từ YouTube/Google Search sang TikTok."

                ## 🏆 III. Toàn Cảnh Doanh Thu & Định Vị Sản Phẩm
                Bảng doanh thu chi tiết (định dạng 48,000,000,000 VNĐ).
                🚨🚨🚨 BCG MATRIX — QUY TẮC NGHIÊM NGẶT 🚨🚨🚨
                Mỗi dòng trong bảng BCG PHẢI dùng CHÍNH XÁC tên model_name từ dữ liệu SQL.
                ❌ SAI: '| Điện tử | 1,500,000,000 | Star | 60% |'
                ❌ SAI: '| Smartphone | 2,000,000,000 | Cash Cow | 40% |'
                ✅ ĐÚNG: '| Galaxy A56 | 141,066,000,000 | Star | 45% |'
                ✅ ĐÚNG: '| Find X9 Pro | 16,860,000,000 | Question Mark | 5% |'
                Nếu dữ liệu SQL có model_name là 'iPhone 17 Pro', bạn PHẢI viết 'iPhone 17 Pro'.

                SAU BẢNG — Phân tích bắt buộc:
                - Phân nhóm BCG Matrix: Star / Cash Cow / Question Mark / Dog cho từng sản phẩm specifc.
                - Xác định "Key Driver" (sản phẩm đóng góp >40% tổng doanh thu) và "Dead Weight"
                  (sản phẩm <10% doanh thu nhưng chiếm nhiều nguồn lực tiếp thị).
                - Gap Analysis: Chênh lệch doanh thu giữa Sản phẩm #1 và #2 là bao nhiêu % ?
                  Con số này nói gì về mức độ phụ thuộc vào một sản phẩm đơn lẻ (Concentration Risk)?
                - Khu vực: Phân tích bất đối xứng địa lý — khu vực nào đang underperform so với GDP/dân số?

                ## ⚔️ IV. Cạnh Tranh Chiến Lược & Benchmark Đối Đầu
                Trình bày bảng benchmarking đối thủ (từ research context).
                SAU BẢNG — Phân tích Win/Loss:
                - Với mỗi đối thủ, phân tích theo cặp (Head-to-Head):
                  "Thắng ở [X] vì [lý do + số liệu] nhưng Thua ở [Y] vì [lý do + số liệu]."
                - Xác định 1 "Gót chân Achilles" chiến lược nhất của đối thủ mạnh nhất
                  mà chúng ta có thể khai thác ngay.
                - Đề xuất "Flanking Strategy" (chiến lược đánh bên sườn):
                  Thay vì đối đầu trực diện về [X], tấn công vào [Y] — nơi đối thủ yếu nhất.

                ## 📱 V. Chiến Lược Nội Dung Truyền Thông Xứng Tầm
                Trình bày 03 phương án nội dung từ Brand Strategist (context).
                ⚠️ YÊU CẦU ĐẶC BIỆT: KHÔNG chỉ copy 1 câu slogan. Mỗi phương án PHẢI có đủ 4 thành phần AIDA,
                mỗi thành phần là 1 ĐOẠN VĂN 3-4 CÂU (không phải 1 câu ngắn):
                - **[A] Attention (Thu hút)**: 3-4 câu — Hook mạnh + Số liệu gây sốc + Pain point.
                - **[I] Interest (Gợi mở)**: 3-4 câu — Thông số kỹ thuật + So sánh tinh tế với đối thủ.
                - **[D] Desire (Khao khát)**: 3-4 câu — Viễn cảnh sở hữu + Ngôn ngữ cảm xúc đẳng cấp.
                - **[A] Action (Hành động)**: 2-3 câu — CTA cụ thể + kênh + ưu đãi độc quyền.

                ## 🗺️ VI. Lộ Trình Triển Khai 7 Ngày (Implementation Roadmap)
                Bảng kế hoạch:
                | Ngày | Hành Động Chiến Lược | Kênh | KPI Mục Tiêu | Ngân Sách | Khu Vực |
                Rules:
                - Mỗi ngày có KPI đo lường cụ thể (VD: "Reach ≥500K", "CTR ≥2.5%", "Leads ≥200").
                - Ngân sách: Format 50,000,000 VNĐ.
                - Khu vực: Chỉ sử dụng {_REGIONS}.
                - Ngày 7 là "Review & Optimize" — tổng ngân sách đã chi, KPI đạt/chưa đạt.

                ## ⚠️ VII. Quản Trị Rủi Ro & Điểm Kiểm Soát (Risk Management)
                ⚠️ KHÔNG ĐƯỢC viết rủi ro chung chung, tautological, hoặc hiển nhiên.
                ❌ CẤM kiểu: "Rủi ro: Doanh thu giảm → Phương án: Tăng cường nguồn lực"
                ❌ CẤM kiểu: "Rủi ro: Cạnh tranh tăng → Phương án: Cạnh tranh mạnh hơn"
                ❌ CẤM kiểu: "Rủi ro: Thay đổi thị trường → Phương án: Nghiên cứu thị trường"
                Mỗi rủi ro PHẢI cụ thể, bất ngờ, và có kế hoạch hành động chi tiết (≥3 rủi ro).

                VÍ DỤ MẪU ĐỂ THAM KHẢO (viết theo phong cách này, KHÔNG copy nguyên văn):

                **Rủi ro #1: Apple giảm giá iPhone 17 Pro trong chương trình Back-to-School**
                - 🎯 Trigger: Apple công bố giảm 15% giá iPhone 17 Pro cho sinh viên, kéo giá
                  từ 32,000,000 xuống 27,200,000 VNĐ — trùng phân khúc Galaxy S26 Ultra.
                - 📊 Xác suất: Cao — Apple đã triển khai chương trình Education Pricing tại 6 thị trường
                  châu Á trong Q2/2025.
                - 💥 Impact: Mất 15-20% thị phần phân khúc 25-32 triệu VNĐ tại khu vực South.
                - 🛡️ Contingency: Kích hoạt chương trình Trade-in bù giá 3,000,000 VNĐ trong 48h.
                  Ngân sách dự phòng: 500,000,000 VNĐ từ quỹ Risk Reserve.
                - 📡 Early Warning: Theo dõi search volume 'iPhone giảm giá' trên Google Trends —
                  khi tăng >300% trong 7 ngày, kích hoạt cảnh báo.

                **Rủi ro #2: TikTok thay đổi thuật toán ưu tiên video dài >3 phút**
                - 🎯 Trigger: TikTok cập nhật thuật toán feed, giảm 40% reach cho video <60 giây.
                - 📊 Xác suất: Trung bình — TikTok đã thử nghiệm tại Indonesia trong tháng 3/2026.
                - 💥 Impact: ROI kênh TikTok có thể giảm từ 1,383 xuống ~800, ảnh hưởng chiến lược Rocket.
                - 🛡️ Contingency: Chuyển 30% ngân sách TikTok sang Instagram Reels trong 72h.
                  Đồng thời sản xuất 5 video dài 3-5 phút từ content dạng mini-series.
                  Ngân sách chuyển đổi nội dung: 100,000,000 VNĐ.
                - 📡 Early Warning: Theo dõi CPM và CTR hàng ngày — khi CPM tăng >25% trong 3 ngày liên tiếp,
                  kích hoạt họp khẩn cấp.

                **Rủi ro #3: Thiếu hụt chip Snapdragon 8 Gen 5 do căng thẳng chuỗi cung ứng TSMC**
                - 🎯 Trigger: TSMC thông báo giảm 20% công suất nhà máy N3P do bảo trì khẩn cấp.
                - 📊 Xác suất: Thấp — nhưng tác động cực lớn nếu xảy ra (Black Swan).
                - 💥 Impact: Gián đoạn nguồn cung Galaxy S26 Ultra tại thị trường Việt Nam trong 4-6 tuần.
                - 🛡️ Contingency: Đẩy mạnh tiêu thụ Galaxy A56 (tồn kho dồi dào) và chạy chương trình
                  Pre-order Galaxy S26 Ultra với ưu đãi giữ chỗ. Ngân sách dự phòng: 300,000,000 VNĐ.
                - 📡 Early Warning: Theo dõi lead time từ nhà cung cấp — khi tăng >50%, báo cáo ngay.

                ⚠️ YÊU CẦU QUY CHUẨN TOÀN BÁO CÁO:
                - Tiếng Việt 100% chuẩn mực văn phong quản trị cấp cao.
                - Tuyệt đối không sử dụng slang, từ ngữ dân dã hoặc các biểu cảm tiêu cực.
                - Toàn bộ báo cáo ≥ 1500 từ.
                - Tiền tệ: Luôn format 48,000,000,000 VNĐ (có dấu phẩy phân cách nghìn).
            """),
            expected_output=dedent(f"""
                # BÁO CÁO CHIẾN LƯỢC EXECUTIVE EXCELLENCE — [Ngày]

                ## 🔭 I. Tổng Quan Chiến Lược & Phân Tích Đa Chiều
                [Đoạn mở đầu 3 câu: Vị thế → Mâu thuẫn → Chủ đề chiến lược]

                **Q1: Động lực tăng trưởng chính?**
                [Trả lời với số liệu cụ thể, ≥3 câu]
                **Q2: Khoảng trống cạnh tranh có thể khai thác?**
                [Trả lời với số liệu cụ thể, ≥3 câu]
                **Q3: Rủi ro lớn nhất và phương án phòng thủ?**
                [Trả lời với số liệu cụ thể, ≥3 câu]

                ---
                ## 📊 II. Phân Tích Hiệu Quả Tài Chính & Tối Ưu Hóa Nguồn Lực
                | Kênh | ROI | CPA | Budget | Phân loại |
                |---|---|---|---|---|
                [Dữ liệu]

                **Ma trận ROI × Budget:**
                🚀 Rocket: [Kênh] — ROI [X] nhưng Budget chỉ [Y]. Đề xuất: [Hành động + số tiền cụ thể]
                🐢 Turtle: [Kênh] — ROI [X] nhưng Budget [Y]. Đề xuất: [Hành động + số tiền cụ thể]
                **Đề xuất tái cấu trúc:** "Chuyển [X] tỷ từ [A] sang [B] vì..."

                ---
                ## 🏆 III. Toàn Cảnh Doanh Thu & Định Vị Sản Phẩm
                | Model | Doanh Thu | Phân loại BCG | Đóng góp % |
                [Dữ liệu + BCG Matrix]

                **Key Driver Analysis:** [Model #1] chiếm [X]% tổng doanh thu — [So What?]
                **Concentration Risk:** Chênh lệch #1 vs #2 là [Y]% — [Why So? + Now What?]
                **Bất đối xứng địa lý:** Khu vực [Z] chiếm [W]% dân số nhưng chỉ [V]% doanh thu — [Hành động]

                ---
                ## ⚔️ IV. Cạnh Tranh Chiến Lược & Benchmark Đối Đầu
                | Đối Thủ | Model | Giá | Thắng | Thua |
                [Bảng Head-to-Head]

                **Gót chân Achilles chiến lược:** [Đối thủ X] yếu nhất ở [Y] — cơ hội khai thác: [Hành động]
                **Flanking Strategy:** [Chiến lược cụ thể]

                ---
                ## 📱 V. Chiến Lược Nội Dung Truyền Thông Xứng Tầm
                ### Phương án 1 — 🛡️ Giải Pháp Chiến Lược
                **[A] Attention:** [≥2 câu — Hook + Số liệu gây sốc]
                **[I] Interest:** [≥2 câu — Giá trị kỹ thuật + So sánh tinh tế]
                **[D] Desire:** [≥2 câu — Viễn cảnh sở hữu]
                **[A] Action:** [CTA + Kênh + Ưu đãi]
                [Lặp lại cho Phương án 2, 3]

                ---
                ## 🗺️ VI. Lộ Trình Triển Khai 7 Ngày
                | Ngày | Hành Động | Kênh | KPI Mục Tiêu | Ngân Sách | Khu Vực |
                |---|---|---|---|---|---|
                | 1 | ... | ... | Reach ≥500K | 50,000,000 VNĐ | North |
                [...]
                | 7 | Review & Optimize | — | Tổng kết KPI | — | All |

                ---
                ## ⚠️ VII. Quản Trị Rủi Ro & Điểm Kiểm Soát
                **Rủi ro #1: [Tên cụ thể]**
                - 🎯 Trigger: [Sự kiện cụ thể]
                - 📊 Xác suất: [Cao/TB/Thấp] — Bằng chứng: [...]
                - 💥 Impact: [Tác động cụ thể]
                - 🛡️ Contingency: [Hành động + Ngân sách dự phòng]
                - 📡 Early Warning: [Chỉ số theo dõi]
                [Lặp lại cho Rủi ro #2, #3]
            """),
            agent=agent,
            context=[research_task, content_task, data_fetch_task],
            tools=tools,
        )

    # ══════════════════════════════════════════════════════════════════════════
    # STAGE 4 — SIGNAL UPDATE (Feedback Loop — Dedicated Task)
    # ══════════════════════════════════════════════════════════════════════════

    def signal_update_task(
        self, agent, report_task: Task, tools: List[BaseTool]
    ) -> Task:
        """Dedicated task to guarantee Signal Update execution after reporting."""
        return Task(
            description=dedent("""
                NHIỆM VỤ: Ghi nhận Bài học Chiến lược (Learning Signals) từ chu kỳ phân tích vừa hoàn thành.

                Đây là bước CUỐI CÙNG, BẮT BUỘC trong pipeline. Bạn PHẢI sử dụng công cụ `signal_update`
                để lưu lại các nhận định quan trọng nhất từ báo cáo vừa hoàn thành.

                HÀNH ĐỘNG CỤ THỂ — Gọi công cụ `signal_update` ÍT NHẤT 3 LẦN với các nội dung sau:

                LẦN 1 — insight_type: "low_performer"
                    Xác định từ context: Model hoặc kênh marketing nào có hiệu suất thấp nhất?
                    Ghi rõ tên model/kênh, chỉ số cụ thể, và đề xuất hành động.

                LẦN 2 — insight_type: "budget_realloc"
                    Xác định từ context: Kênh nào có ROI cao nhưng ngân sách thấp (cần tăng)?
                    Kênh nào có ROI thấp nhưng ngân sách cao (cần giảm)?
                    Ghi rõ tên kênh, ROI, budget, và đề xuất tái phân bổ.

                LẦN 3 — insight_type: "trend_alert"
                    Xác định từ context: Xu hướng thị trường hoặc phản hồi khách hàng nào
                    cần được theo dõi trong chu kỳ tiếp theo?
                    Ghi rõ xu hướng, nguồn dữ liệu, và mức độ ưu tiên.

                ⚠️ QUY TẮC:
                - BẮT BUỘC gọi signal_update ít nhất 3 lần.
                - Mỗi lần gọi phải có insight_type khác nhau.
                - learning_content phải trích dẫn số liệu cụ thể từ báo cáo.
                - Trả Final Answer SAU KHI đã gọi đủ 3 lần signal_update.
            """),
            expected_output=dedent("""
                ## 📡 SIGNAL UPDATES — Bài Học Chiến Lược Đã Ghi Nhận

                ✅ Signal 1 — [low_performer]: [Mô tả ngắn]
                ✅ Signal 2 — [budget_realloc]: [Mô tả ngắn]
                ✅ Signal 3 — [trend_alert]: [Mô tả ngắn]

                Tổng cộng: 3 bài học chiến lược đã được lưu vào learning_signals database.
            """),
            agent=agent,
            context=[report_task],
            tools=tools,
        )
