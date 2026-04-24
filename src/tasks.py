"""
MarketingTasks — Pipeline 4 stages theo chuẩn Executive Strategic Reporting.
Nâng cấp: Chain-of-Thought Reasoning, SWOT/PESTEL/Forecasting,
          Segment-based Content (Gen Z / Doanh nhân / Phổ thông).
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
    # STAGE 1 — TÌNH BÁO THỊ TRƯỜNG & COMPETITOR BENCHMARKING
    # ══════════════════════════════════════════════════════════════════════════

    def research_task(self, agent, market_topic: str) -> Task:
        return Task(
            description=dedent(f"""
                NHIỆM VỤ: Competitor Benchmarking & Market Intelligence — Phân tích {market_topic}

                {_REGION_NOTE}

                📐 PHƯƠNG PHÁP SUY LUẬN (Chain-of-Thought — Tuân thủ nghiêm ngặt):
                Với MỖI bước bên dưới, bạn PHẢI suy luận theo 3 giai đoạn:
                  (a) THU THẬP: Gọi SQL hoặc Search để lấy dữ liệu thô.
                  (b) PHÂN TÍCH: Đọc dữ liệu → xác định pattern, anomaly, và gap.
                  (c) KẾT LUẬN: Đưa ra 1 nhận định chiến lược dựa trên bằng chứng.

                ═══════════════════════════════════════════════
                BƯỚC 1 — BENCHMARKING ĐỐI THỦ (Bắt buộc SQL + Internet Search)
                ═══════════════════════════════════════════════

                1A. Truy vấn SQL — Dữ liệu nội bộ:
                    SELECT brand, model_name, key_features, current_price,
                           strengths, weaknesses
                    FROM competitor_products
                    ORDER BY current_price DESC
                    LIMIT 8

                1B. Internet Search — Dữ liệu thị trường VN thực tế:
                    Tìm kiếm CỤ THỂ 3 chủ đề sau (mỗi chủ đề 1 lần search riêng):
                    - "Giá bán thực tế [model_name] tại Việt Nam 2026 Shopee TGDĐ"
                    - "Đánh giá [model_name] review người dùng Việt Nam"
                    - "So sánh cấu hình smartphone flagship 2026 Việt Nam"

                1C. Suy luận — Đối chiếu nội bộ vs thị trường:
                    - Giá nội bộ (current_price) khác giá thực tế bao nhiêu %?
                    - Điểm mạnh/yếu trong SQL có khớp với phản hồi người dùng thực tế không?

                Xuất bảng ENRICHED (kết hợp SQL + Search):
                | Đối Thủ | Model | Cấu hình (Chip/Camera/Pin) | Giá Niêm Yết (VNĐ) | Giá Thực Tế VN | Lợi Thế | Gót Chân Achilles | Phản hồi Người dùng VN |

                ═══════════════════════════════════════════════
                BƯỚC 2 — MODEL DẪN ĐẦU DOANH THU (Bắt buộc SQL)
                ═══════════════════════════════════════════════

                    SELECT model_name, SUM(units_sold * unit_price) AS revenue,
                           SUM(units_sold) AS total_units
                    FROM sales
                    GROUP BY model_name
                    ORDER BY revenue DESC
                    LIMIT 5

                Suy luận:
                → Model #1 dẫn đầu vì lý do gì? (Giá cao? Volume lớn? Cả hai?)
                → Gap giữa #1 và #2 có đáng lo ngại về Concentration Risk không?

                ═══════════════════════════════════════════════
                BƯỚC 3 — CẤU HÌNH KỸ THUẬT CHI TIẾT (Internet Search)
                ═══════════════════════════════════════════════

                Tìm kiếm và tổng hợp bảng so sánh cấu hình (≥4 models từ Bước 1):
                | Model | Chipset (AnTuTu) | Camera Chính | Pin (mAh) + Sạc (W) | Màn hình (Hz/nits) | RAM/ROM |

                Suy luận:
                → Model nào có cấu hình vượt trội nhất ở MỖI tiêu chí?
                → Model nào "thua" về spec nhưng thắng về doanh thu? Tại sao?

                ═══════════════════════════════════════════════
                BƯỚC 4 — PHẢN HỒI NGƯỜI DÙNG VIỆT NAM (SQL + Search)
                ═══════════════════════════════════════════════

                4A. SQL — Social Sentiment nội bộ:
                    SELECT keyword, top_complaint, negative_score,
                           positive_score, total_mentions, trending_platform
                    FROM social_sentiment
                    ORDER BY negative_score DESC
                    LIMIT 5

                4B. Internet Search — Review thực tế:
                    Tìm "phàn nàn phổ biến nhất [top model] tại Việt Nam 2026"

                4C. Suy luận — Tổng hợp phản hồi:
                    Xuất bảng:
                    | Model | Top 3 Lời khen | Top 3 Phàn nàn | Điểm đánh giá TB | Nguồn |

                ═══════════════════════════════════════════════
                BƯỚC 5 — SẢN PHẨM HIỆU SUẤT THẤP (Bắt buộc SQL)
                ═══════════════════════════════════════════════

                    SELECT model_name, region, SUM(units_sold) AS total_units,
                           ROUND(AVG(unit_price), 0) AS avg_price
                    FROM sales
                    GROUP BY model_name, region
                    ORDER BY total_units ASC
                    LIMIT 3

                Suy luận:
                → Model nào đang underperform? Tại khu vực nào?
                → Nguyên nhân có phải do giá, do kênh phân phối, hay do đối thủ?

                ═══════════════════════════════════════════════
                BƯỚC 6 — XU HƯỚNG THỊ TRƯỜNG (Internet Search)
                ═══════════════════════════════════════════════

                Tìm 3 xu hướng đang định hình thị trường smartphone Việt Nam:
                - Xu hướng 1: Công nghệ (AI Phone, foldable, satellite, v.v.)
                - Xu hướng 2: Hành vi tiêu dùng (mua trả góp, TMĐT, v.v.)
                - Xu hướng 3: Chính sách/Pháp lý (thuế nhập khẩu, bảo hành, v.v.)

                ⚠️ QUY TẮC SQL & ĐỊNH DẠNG:
                - Model: model_name | Giá: unit_price hoặc current_price.
                - Định dạng số: Luôn có dấu phẩy phân cách (ví dụ: 12,500,000 VNĐ).
                - Khu vực: Tuyệt đối chỉ dùng {_REGIONS}.
            """),
            expected_output=dedent("""
                ## 🛡️ I. Bảng Benchmarking Đối Thủ Enriched (SQL + Market Data)
                | Đối Thủ | Model | Cấu hình | Giá Niêm Yết | Giá Thực Tế VN | Lợi Thế | Gót Chân Achilles | Phản hồi VN |
                (Dữ liệu thực tế, định dạng 32,000,000 VNĐ)

                ## 📈 II. Bảng Xếp hạng Doanh Thu (Top 5 Models)
                | Model | Doanh Thu | Số lượng | Phân tích Gap |
                *Suy luận: [Model #1] dẫn đầu vì [lý do] — Gap vs #2 là [X]%*

                ## ⚙️ III. So Sánh Cấu Hình Kỹ Thuật Chi Tiết
                | Model | Chipset | Camera | Pin + Sạc | Màn hình | RAM/ROM |
                *Suy luận: [Model X] vượt trội về [Y] nhưng thua [Z] về [W]*

                ## 👥 IV. Phản Hồi Người Dùng Việt Nam (Social Listening + Review)
                | Model | Top 3 Lời khen | Top 3 Phàn nàn | Điểm TB | Nguồn |
                *Suy luận: Pain point phổ biến nhất là [X] — cơ hội khai thác: [Y]*

                ## 📉 V. Danh Mục Sản Phẩm Cần Cải Thiện
                | model_name | region | total_units | avg_price |
                *Suy luận: [Model] đang underperform tại [Region] vì [lý do]*

                ## 🚀 VI. Xu Hướng Thị Trường Key Insights
                - Xu hướng 1 (Công nghệ): [Mô tả + Impact]
                - Xu hướng 2 (Hành vi): [Mô tả + Impact]
                - Xu hướng 3 (Chính sách): [Mô tả + Impact]
            """),
            agent=agent,
        )

    # ══════════════════════════════════════════════════════════════════════════
    # STAGE 1.5 — CREATIVE DECISION LAYER (Tầng Ra quyết định Sáng tạo)
    # ══════════════════════════════════════════════════════════════════════════

    def creative_decision_task(self, agent, research_task: Task) -> Task:
        """Decision Layer: Chuyển hóa dữ liệu thô thành Creative Brief theo phân khúc."""
        return Task(
            description=dedent(f"""
                NHIỆM VỤ: Creative Director — Phân tích kết quả nghiên cứu và ra quyết định
                định hướng sáng tạo THEO PHÂN KHÚC KHÁCH HÀNG.

                Bạn KHÔNG viết nội dung marketing. Bạn CHỈ ra quyết định chiến lược sáng tạo.
                Đọc kỹ toàn bộ output từ Intelligence Lead (research_task) và xây dựng một CREATIVE BRIEF
                có cấu trúc chặt chẽ, PHÂN TÁCH RÕ RÀNG cho 3 phân khúc.

                {_REGION_NOTE}

                📐 PHƯƠNG PHÁP SUY LUẬN (Chain-of-Thought):
                BƯỚC 1: Đọc research context → Liệt kê 5 data points quan trọng nhất.
                BƯỚC 2: Phân loại từng data point: "Insight này hấp dẫn nhất với phân khúc nào?"
                BƯỚC 3: Thiết kế Tone/Angle/Message RIÊNG cho từng phân khúc.
                BƯỚC 4: Xuất Creative Brief có cấu trúc rõ ràng.

                ═══════════════════════════════════════════════
                PHÂN TÍCH BẮT BUỘC
                ═══════════════════════════════════════════════

                A. DATA INSIGHT EXTRACTION (Rút trích Insight từ dữ liệu):
                   - Xác định Top 1 model dẫn đầu doanh thu và lý do (từ context).
                   - Xác định Top 1 model hiệu suất thấp nhất và nguyên nhân (từ context).
                   - Xác định Top 1 complaint nghiêm trọng nhất từ Social Sentiment (từ context).
                   - Xác định 1-2 điểm yếu nổi bật nhất của đối thủ (từ benchmarking context).
                   - Xác định cấu hình kỹ thuật nào là lợi thế vượt trội nhất (từ spec comparison).
                   - Tổng hợp phản hồi người dùng VN: Pain point + Delight factor chung.

                B. CREATIVE DECISIONS THEO 3 PHÂN KHÚC:

                   ═══════════════════════════════════════
                   PHÂN KHÚC 1: 🎯 GEN Z (18-25 tuổi)
                   ═══════════════════════════════════════
                   - Đặc điểm: Digital native, theo trend, coi trọng thiết kế & camera,
                     mua hàng qua TMĐT, thanh toán trả góp, bị ảnh hưởng bởi KOL.
                   - Giọng điệu khuyến nghị: Năng động, ngang hàng, dùng số liệu wow.
                   - Góc tiếp cận: Từ benchmarking, chọn angle nào hấp dẫn Gen Z nhất?
                   - Kênh ưu tiên: TikTok (ROI {_ROI_DATA.split(',')[0]}), Instagram.
                   - Key Message: Câu ngắn, gây tò mò, dễ share.

                   ═══════════════════════════════════════
                   PHÂN KHÚC 2: 💼 DOANH NHÂN (30-45 tuổi)
                   ═══════════════════════════════════════
                   - Đặc điểm: Coi trọng hiệu suất, bảo mật, đẳng cấp & hệ sinh thái,
                     sẵn sàng trả giá cao, mua tại cửa hàng brand, thanh toán thẻ tín dụng.
                   - Giọng điệu khuyến nghị: Tinh tế, premium, nhấn mạnh productivity.
                   - Góc tiếp cận: Từ benchmarking, chọn angle nào thuyết phục Doanh nhân?
                   - Kênh ưu tiên: YouTube (long-form review), Google Search (intent-based).
                   - Key Message: Nhấn mạnh ROI cá nhân, thời gian tiết kiệm, đẳng cấp.

                   ═══════════════════════════════════════
                   PHÂN KHÚC 3: 👨‍👩‍👧‍👦 PHỔ THÔNG (25-40 tuổi)
                   ═══════════════════════════════════════
                   - Đặc điểm: Coi trọng giá trị/giá tiền, bền bỉ, pin trâu,
                     so sánh kỹ trước khi mua, bị ảnh hưởng bởi review YouTube & Facebook.
                   - Giọng điệu khuyến nghị: Thực tế, so sánh rõ ràng, dễ hiểu.
                   - Góc tiếp cận: Từ benchmarking, chọn angle nào thuyết phục Phổ thông?
                   - Kênh ưu tiên: Facebook (ROI {_ROI_DATA.split(',')[2]}), KOL review.
                   - Key Message: "Được nhiều hơn, trả ít hơn" — value proposition rõ ràng.

                C. TỔNG HỢP KÊNH TRUYỀN THÔNG:
                   - Dựa trên dữ liệu ROI: {_ROI_DATA}
                   - Phân bổ kênh theo phân khúc — KHÔNG dùng 1 kênh cho tất cả.

                ⚠️ QUY TẮC:
                - Mọi quyết định PHẢI trích dẫn số liệu cụ thể từ context.
                - KHÔNG viết nội dung marketing, KHÔNG viết post, KHÔNG viết caption.
                - Đầu ra là một Creative Brief dạng bảng có cấu trúc rõ ràng THEO PHÂN KHÚC.
            """),
            expected_output=dedent("""
                # 🎯 CREATIVE BRIEF — CHIẾN LƯỢC ĐỊNH HƯỚNG SÁNG TẠO THEO PHÂN KHÚC

                ## A. DATA INSIGHTS DASHBOARD
                | Chỉ số | Giá trị | Nguồn |
                |---|---|---|
                | Model dẫn đầu doanh thu | [model_name] — [revenue] VNĐ | SQL: sales |
                | Model hiệu suất thấp | [model_name] — [units] units | SQL: sales |
                | Top complaint | [complaint] — Score: [score] | SQL: social_sentiment |
                | Điểm yếu đối thủ chiến lược | [brand] — [weakness] | SQL: competitor_products |
                | Cấu hình vượt trội nhất | [model] — [spec detail] | Internet Search |
                | Phản hồi người dùng VN | [Top khen] / [Top phàn nàn] | Review + SQL |

                ## B. CREATIVE BRIEF — PHÂN KHÚC GEN Z 🎯
                | Yếu tố | Quyết định | Cơ sở dữ liệu |
                |---|---|---|
                | Tone | [Tone cho Gen Z] | [Data backing] |
                | Angle | [Angle cho Gen Z] | [Data backing] |
                | Key Message | [Message cho Gen Z] | [Data backing] |
                | Kênh ưu tiên | TikTok, Instagram | ROI data |
                | CTA Style | [Mô tả] | Persona insight |

                ## C. CREATIVE BRIEF — PHÂN KHÚC DOANH NHÂN 💼
                | Yếu tố | Quyết định | Cơ sở dữ liệu |
                |---|---|---|
                | Tone | [Tone cho Doanh nhân] | [Data backing] |
                | Angle | [Angle cho Doanh nhân] | [Data backing] |
                | Key Message | [Message cho Doanh nhân] | [Data backing] |
                | Kênh ưu tiên | YouTube, Google Search | ROI data |
                | CTA Style | [Mô tả] | Persona insight |

                ## D. CREATIVE BRIEF — PHÂN KHÚC PHỔ THÔNG 👨‍👩‍👧‍👦
                | Yếu tố | Quyết định | Cơ sở dữ liệu |
                |---|---|---|
                | Tone | [Tone cho Phổ thông] | [Data backing] |
                | Angle | [Angle cho Phổ thông] | [Data backing] |
                | Key Message | [Message cho Phổ thông] | [Data backing] |
                | Kênh ưu tiên | Facebook, KOL | ROI data |
                | CTA Style | [Mô tả] | Persona insight |
            """),
            agent=agent,
            context=[research_task],
        )

    # ══════════════════════════════════════════════════════════════════════════
    # STAGE 2 — SÁNG TẠO NỘI DUNG THEO PHÂN KHÚC KHÁCH HÀNG (AIDA EXECUTIVE)
    # ══════════════════════════════════════════════════════════════════════════

    def content_creation_task(self, agent, creative_decision_task: Task) -> Task:
        """Content execution theo phân khúc: Gen Z, Doanh nhân, Phổ thông."""
        return Task(
            description=dedent("""
                NHIỆM VỤ: Brand Strategist — Xây dựng 03 BỘ NỘI DUNG AIDA RIÊNG BIỆT
                cho 3 phân khúc khách hàng: Gen Z, Doanh nhân, Người dùng Phổ thông.

                ⚠️ QUAN TRỌNG: Bạn PHẢI tuân thủ 100% Creative Brief từ Creative Director.
                KHÔNG tự diễn giải dữ liệu thô. Mọi quyết định về giọng điệu, góc tiếp cận,
                đối tượng mục tiêu và thông điệp đã được Creative Director quyết định.

                📐 PHƯƠNG PHÁP SUY LUẬN (Chain-of-Thought):
                BƯỚC 1: Đọc Creative Brief → Liệt kê quyết định cho từng phân khúc.
                BƯỚC 2: Tự hỏi "Persona này quan tâm điều gì NHẤT?" → Ưu tiên yếu tố đó trong Hook.
                BƯỚC 3: Viết AIDA với ngôn ngữ PHÙ HỢP persona — Gen Z ≠ Doanh nhân ≠ Phổ thông.
                BƯỚC 4: Chọn kênh + CTA phù hợp với hành vi mua hàng của từng persona.

                ═══════════════════════════════════════════════════
                PHÂN KHÚC 1: 🎯 GEN Z (18-25 tuổi)
                ═══════════════════════════════════════════════════
                *Tuân theo Creative Brief — Phân khúc Gen Z*

                Đặc điểm ngôn ngữ Gen Z:
                - Ngắn gọn, punchy, dùng số liệu WOW ngay câu đầu.
                - Tone ngang hàng, không lên lớp, không quá formal.
                - Dùng emoji tự nhiên, hashtags viral.
                - Tập trung vào: Camera, Design, Gaming, Social media experience.

                **[HOOK]**: 3-4 câu — Mở bằng con số gây sốc hoặc câu hỏi provocative.
                    VD: "97% Gen Z chọn điện thoại vì camera — nhưng chỉ 1 model vừa phá kỷ lục DxOMark."
                **[BODY]**: 3-4 câu — Spec nổi bật nhất cho Gen Z (camera, design, gaming performance).
                    So sánh ngắn gọn với đối thủ bằng con số cụ thể.
                **[DESIRE]**: 3-4 câu — Viễn cảnh "flex" trên social, content creation chuyên nghiệp.
                **[CTA]**: 2-3 câu — Link Shopee/Lazada, mã giảm giá, trả góp 0%.
                **[CHANNEL]**: TikTok (video 30s), Instagram Reels, Shopee Live.
                **[HASHTAGS]**: 10 hashtags trending, viral-ready.

                ═══════════════════════════════════════════════════
                PHÂN KHÚC 2: 💼 DOANH NHÂN (30-45 tuổi)
                ═══════════════════════════════════════════════════
                *Tuân theo Creative Brief — Phân khúc Doanh nhân*

                Đặc điểm ngôn ngữ Doanh nhân:
                - Tinh tế, chuyên nghiệp, nhấn mạnh ROI cá nhân.
                - Tone đẳng cấp, tập trung vào giá trị thay vì giá tiền.
                - Không dùng emoji quá nhiều, ưu tiên nội dung long-form.
                - Tập trung vào: Hiệu suất, Bảo mật, Hệ sinh thái, Đẳng cấp.

                **[HOOK]**: 3-4 câu — Mở bằng insight về productivity hoặc competitive advantage.
                    VD: "CEO nào cũng biết: 30 phút tiết kiệm mỗi ngày = 182 giờ/năm. Một thiết bị đúng đắn
                    tạo ra chênh lệch đó."
                **[BODY]**: 3-4 câu — Hiệu suất chip, bảo mật enterprise, hệ sinh thái đa thiết bị.
                    Dẫn chứng từ benchmark hoặc case study.
                **[DESIRE]**: 3-4 câu — Hình ảnh người lãnh đạo sử dụng công nghệ để dẫn đầu.
                    Đẳng cấp, exclusive, không phải ai cũng sở hữu.
                **[CTA]**: 2-3 câu — Đặt lịch tư vấn 1:1, trải nghiệm tại showroom premium, trade-in VIP.
                **[CHANNEL]**: YouTube (review 10 phút), LinkedIn Article, Email newsletter.
                **[HASHTAGS]**: 10 hashtags chuyên nghiệp, B2B-friendly.

                ═══════════════════════════════════════════════════
                PHÂN KHÚC 3: 👨‍👩‍👧‍👦 PHỔ THÔNG (25-40 tuổi)
                ═══════════════════════════════════════════════════
                *Tuân theo Creative Brief — Phân khúc Phổ thông*

                Đặc điểm ngôn ngữ Phổ thông:
                - Thực tế, dễ hiểu, tập trung vào giá trị/giá tiền.
                - Tone gần gũi nhưng vẫn chuyên nghiệp.
                - So sánh trực tiếp, bảng spec dễ đọc.
                - Tập trung vào: Pin trâu, Bền bỉ, Giá hợp lý, Bảo hành tốt.

                **[HOOK]**: 3-4 câu — Mở bằng comparison trực tiếp hoặc testimonial.
                    VD: "Cùng phân khúc 10 triệu, một bên pin 4000mAh, một bên 5500mAh.
                    Lựa chọn nào thông minh hơn đã rõ ràng."
                **[BODY]**: 3-4 câu — Bảng so sánh đơn giản: Model A vs Model B vs Model C.
                    Nhấn mạnh value-for-money từ dữ liệu thực tế.
                **[DESIRE]**: 3-4 câu — Gia đình hài lòng, sản phẩm bền, không phải sửa chữa.
                    Đầu tư 1 lần — sử dụng bền bỉ 3 năm.
                **[CTA]**: 2-3 câu — Các ưu đãi thực tế: giảm giá, tặng kèm, bảo hành mở rộng.
                **[CHANNEL]**: Facebook (post + group review), Zalo OA, KOL review YouTube.
                **[HASHTAGS]**: 10 hashtags phổ thông, dễ tìm.

                ⚠️ QUY TẮC NGÔN NGỮ & ĐỊNH DẠNG:
                1. 100% tiếng Việt có dấu, đúng ngữ pháp và dấu câu.
                   ⛔ CẤM ký tự Trung Quốc (面臨, 市場), Nhật, Hàn, hoặc tiếng Anh
                   (trừ thuật ngữ kỹ thuật: ROI, CPA, KPI, AIDA, CTR, KOL, Trade-in).
                2. Sử dụng Emoji tinh tế (📈, 💎, 🛡️, 🤝).
                3. Tiền tệ chuẩn: 16,860,000,000 VNĐ.
                4. Từ ngữ: Chuyên nghiệp, lịch sự, không sử dụng biệt ngữ tiêu cực hoặc từ ngữ dân dã.
                5. Mỗi phân khúc phải ghi rõ: "Tuân theo Creative Brief — Phân khúc: [tên], Tone: [tên tone]".
                6. ĐỘ SÂU BẮT BUỘC: Mỗi thành phần AIDA (Hook, Body, Desire, CTA) PHẢI là
                   1 đoạn văn đầy đủ gồm 3-4 câu chuyên nghiệp, có sức thuyết phục cao.
                   ⛔ CẤM viết 1 câu slogan ngắn rồi dừng lại.
            """),
            expected_output=dedent("""
                # CONTENT MARKETING THEO PHÂN KHÚC KHÁCH HÀNG

                ## 🎯 PHÂN KHÚC 1 — GEN Z (18-25)
                *Tuân theo Creative Brief — Phân khúc: Gen Z, Tone: [Tone]*

                **[HOOK]**: [Đoạn văn 3-4 câu — con số wow, câu hỏi provocative]
                **[BODY]**: [Đoạn văn 3-4 câu — camera, design, gaming spec]
                **[DESIRE]**: [Đoạn văn 3-4 câu — social flex, content creation]
                **[CTA]**: [2-3 câu — Shopee, trả góp, mã giảm giá]
                **[CHANNEL]**: TikTok, Instagram Reels
                **[HASHTAGS]**: (10 hashtags viral)

                ---
                ## 💼 PHÂN KHÚC 2 — DOANH NHÂN (30-45)
                *Tuân theo Creative Brief — Phân khúc: Doanh nhân, Tone: [Tone]*

                **[HOOK]**: [Đoạn văn 3-4 câu — productivity, competitive advantage]
                **[BODY]**: [Đoạn văn 3-4 câu — hiệu suất, bảo mật, hệ sinh thái]
                **[DESIRE]**: [Đoạn văn 3-4 câu — đẳng cấp lãnh đạo]
                **[CTA]**: [2-3 câu — tư vấn 1:1, showroom, trade-in VIP]
                **[CHANNEL]**: YouTube, LinkedIn
                **[HASHTAGS]**: (10 hashtags chuyên nghiệp)

                ---
                ## 👨‍👩‍👧‍👦 PHÂN KHÚC 3 — PHỔ THÔNG (25-40)
                *Tuân theo Creative Brief — Phân khúc: Phổ thông, Tone: [Tone]*

                **[HOOK]**: [Đoạn văn 3-4 câu — comparison, value-for-money]
                **[BODY]**: [Đoạn văn 3-4 câu — bảng so sánh spec, giá]
                **[DESIRE]**: [Đoạn văn 3-4 câu — bền bỉ, gia đình hài lòng]
                **[CTA]**: [2-3 câu — giảm giá, bảo hành, tặng kèm]
                **[CHANNEL]**: Facebook, Zalo, KOL YouTube
                **[HASHTAGS]**: (10 hashtags phổ thông)
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
                Chỉ trả về các bảng Markdown chứa kết quả thô từ SQL, không kèm phân tích.

                {_REGION_NOTE}

                📐 PHƯƠNG PHÁP SUY LUẬN (Chain-of-Thought):
                BƯỚC 1: Xác định 5 bộ dữ liệu cần thiết cho báo cáo Executive.
                BƯỚC 2: Viết SQL cho từng bộ dữ liệu — đảm bảo ORDER BY + LIMIT.
                BƯỚC 3: Trả về kết quả dạng bảng Markdown thuần — không phân tích.

                SQL 1 — Chỉ số ROI & CPA theo kênh (TikTok, Instagram, Facebook, YouTube, Google Search, KOL).
                SQL 2 — Doanh thu phân bổ theo Model (Sắp xếp giảm dần). Dùng SUM(units_sold * unit_price).
                SQL 3 — Doanh thu phân bổ theo Khu vực Địa lý ({_REGIONS}).
                SQL 4 — Doanh thu theo tháng (sales_performance) để phục vụ Forecasting.
                SQL 5 — Phân bổ khách hàng theo nhóm tuổi và phương thức thanh toán (phục vụ SWOT).
            """),
            expected_output="5 bảng Markdown dữ liệu tài chính thô (ROI/CPA, Revenue by Model, Revenue by Region, Monthly Trend, Customer Profile).",
            agent=agent,
            context=[research_task, creative_decision_task, content_task],
        )

    # ══════════════════════════════════════════════════════════════════════════
    # STAGE 3 — BÁO CÁO CHIẾN LƯỢC EXECUTIVE EXCELLENCE
    # (NÂNG CẤP: SWOT + PESTEL + FORECASTING + BCG)
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

                📐 PHƯƠNG PHÁP SUY LUẬN (Chain-of-Thought — Bắt buộc cho MỖI phần):
                Với MỖI phần báo cáo, bạn phải suy luận 4 bước:
                BƯỚC 1 (Thu thập): Lấy dữ liệu từ context hoặc truy vấn SQL bổ sung.
                BƯỚC 2 (Phân tích): Áp dụng framework lên dữ liệu — tìm pattern + anomaly.
                BƯỚC 3 (Suy luận): So What? → Why So? → Now What?
                BƯỚC 4 (Hành động): Chuyển insight thành action item với timeline + KPI.

                ⛔ QUY TẮC TUYỆT ĐỐI — VI PHẠM = BÁO CÁO BỊ TỪ CHỐI:
                1. CẤM đọc lại số liệu đã có trong bảng. Bảng cung cấp DATA — bạn cung cấp INSIGHT.
                2. CẤM bắt đầu câu bằng: "Dựa trên bảng này", "Như chúng ta thấy", "Từ dữ liệu trên",
                   "Bảng trên cho thấy", "Điều này có nghĩa là", "Chúng tôi có thể thấy rằng".
                3. CẤM phân tích đơn chiều. Luôn phân tích GIAO CẮT.
                4. DƯỚI mỗi bảng: BẮT BUỘC viết ≥3 câu phân tích (So What/Why So/Now What).
                5. Toàn bộ báo cáo ≥ 2000 từ. Mỗi phần ≥ 150 từ.

                🚨 HARD GUARDRAIL #6 — NGÔN NGỮ THUẦN KHIẾT:
                Output PHẢI 100% TIẾNG VIỆT. CẤM ký tự Trung Quốc, Nhật, Hàn.
                CẤM Tiếng Anh ngoài thuật ngữ kỹ thuật (ROI, CPA, KPI, BCG, AIDA, CTR,
                Trade-in, KOL, SWOT, PESTEL).

                🚨 HARD GUARDRAIL #7 — TÍNH TOÀN VẸN DỮ LIỆU:
                TUYỆT ĐỐI CẤM gom sản phẩm vào danh mục chung chung.
                BẮT BUỘC dùng CHÍNH XÁC tên model_name từ SQL.

                🚨 HARD GUARDRAIL #8 — CẤM PHÂN TÍCH TAUTOLOGICAL:
                PHẢI viết: Nguyên nhân gốc rễ + hành động cụ thể + số tiền + timeline.

                ═══════════════════════════════════════════════════
                CẤU TRÚC BÁO CÁO — 10 PHẦN CHIẾN LƯỢC
                ═══════════════════════════════════════════════════

                ## 🔭 I. Tổng Quan Chiến Lược & Phân Tích Đa Chiều (Executive Summary)
                Viết 1 đoạn mở đầu có sức nặng như một Partner McKinsey trình bày trước Board of Directors.
                - Câu 1: Khẳng định vị thế hiện tại (dựa trên số liệu doanh thu dẫn đầu).
                - Câu 2: Chỉ ra mâu thuẫn chiến lược lớn nhất.
                - Câu 3: Đề xuất Chủ đề Chiến lược (Strategic Theme) cho kỳ này.
                Sau đó đặt và trả lời 3 câu hỏi chiến lược. Mỗi câu trả lời phải có SỐ LIỆU CỤ THỂ.

                ## 📊 II. Phân Tích Hiệu Quả Tài Chính & Tối Ưu Hóa Nguồn Lực
                Bảng ROI/CPA theo kênh + Ma trận ROI × Budget (Star/Rocket/Turtle/Mystery).
                {_ROI_DATA}

                ## 🏆 III. Toàn Cảnh Doanh Thu & BCG Matrix
                Bảng doanh thu + BCG Matrix (Star/Cash Cow/Question Mark/Dog).
                🚨 Mỗi dòng PHẢI dùng CHÍNH XÁC model_name từ SQL.
                Phân tích: Key Driver, Concentration Risk, Gap Analysis, Bất đối xứng địa lý.

                ## 🔍 IV. MA TRẬN SWOT — PHÂN TÍCH NỘI LỰC & MÔI TRƯỜNG ★★★ MỚI ★★★

                📐 Chain-of-Thought cho SWOT:
                BƯỚC 1: Từ dữ liệu doanh thu + benchmarking → Liệt kê 3-5 Strengths (S).
                BƯỚC 2: Từ sản phẩm underperform + complaint → Liệt kê 3-5 Weaknesses (W).
                BƯỚC 3: Từ xu hướng thị trường + đối thủ yếu → Liệt kê 3-5 Opportunities (O).
                BƯỚC 4: Từ đối thủ mạnh + rủi ro external → Liệt kê 3-5 Threats (T).

                Xuất bảng SWOT:
                | | Yếu tố Tích cực | Yếu tố Tiêu cực |
                |---|---|---|
                | **Nội bộ** | **S - Điểm Mạnh** | **W - Điểm Yếu** |
                | | S1: [Dựa trên doanh thu SQL] | W1: [Dựa trên underperformer SQL] |
                | | S2: [Dựa trên cấu hình benchmarking] | W2: [Dựa trên complaint data] |
                | | S3: [Dựa trên ROI kênh mạnh] | W3: [Dựa trên khu vực yếu] |
                | **Bên ngoài** | **O - Cơ hội** | **T - Thách thức** |
                | | O1: [Dựa trên xu hướng search] | T1: [Dựa trên đối thủ mạnh nhất] |
                | | O2: [Dựa trên điểm yếu đối thủ] | T2: [Dựa trên rủi ro chuỗi cung ứng] |
                | | O3: [Dựa trên phân khúc chưa khai thác] | T3: [Dựa trên thay đổi pháp lý] |

                SAU BẢNG SWOT — Viết CHIẾN LƯỢC GIAO CẮT bắt buộc:
                - **SO (Strengths × Opportunities):** Dùng điểm mạnh nào để khai thác cơ hội nào?
                - **WO (Weaknesses × Opportunities):** Khắc phục điểm yếu nào để nắm bắt cơ hội?
                - **ST (Strengths × Threats):** Dùng điểm mạnh nào để phòng thủ trước thách thức?
                - **WT (Weaknesses × Threats):** Điểm yếu + thách thức nào tạo rủi ro nghiêm trọng nhất?

                ## 🌍 V. PHÂN TÍCH PESTEL — MÔI TRƯỜNG VĨ MÔ THỊ TRƯỜNG SMARTPHONE VN ★★★ MỚI ★★★

                📐 Chain-of-Thought cho PESTEL:
                BƯỚC 1: Với MỖI yếu tố (P-E-S-T-E-L), tìm ít nhất 1 sự kiện/xu hướng CỤ THỂ
                        đang ảnh hưởng đến thị trường smartphone Việt Nam NĂM 2026.
                BƯỚC 2: Đánh giá Impact (Tích cực / Tiêu cực / Trung tính) cho mỗi yếu tố.
                BƯỚC 3: Đề xuất hành động ứng phó cụ thể.

                | Yếu tố | Mô tả Sự kiện/Xu hướng Cụ thể | Impact | Hành động Ứng phó |
                |---|---|---|---|
                | **P** - Chính trị | [VD: Chính sách hỗ trợ sản xuất điện tử nội địa VN] | Tích cực/Tiêu cực | [Hành động] |
                | **E** - Kinh tế | [VD: Tăng trưởng GDP VN 6.5%, thu nhập tầng trung tăng] | ... | [Hành động] |
                | **S** - Xã hội | [VD: Gen Z chiếm 30% lực lượng lao động, ưu tiên trải nghiệm] | ... | [Hành động] |
                | **T** - Công nghệ | [VD: AI Phone, 5G phủ sóng toàn quốc, foldable mainstream] | ... | [Hành động] |
                | **E** - Môi trường | [VD: Xu hướng điện thoại bền vững, vật liệu tái chế] | ... | [Hành động] |
                | **L** - Pháp lý | [VD: Quy định bảo hành 24 tháng, chống hàng xách tay] | ... | [Hành động] |

                SAU BẢNG PESTEL — Viết TÓM TẮT CHIẾN LƯỢC:
                "Yếu tố PESTEL có impact lớn nhất là [X]. Hành động ưu tiên #1: [Mô tả cụ thể]."

                ## 📈 VI. DỰ BÁO XU HƯỚNG (FORECASTING) ★★★ MỚI ★★★

                📐 Chain-of-Thought cho Forecasting:
                BƯỚC 1: Truy vấn SQL để lấy dữ liệu doanh thu theo tháng (sales_performance).
                BƯỚC 2: Xác định trend line — doanh thu đang đi lên, đi xuống, hay đi ngang?
                BƯỚC 3: Kết hợp xu hướng thị trường từ research context + PESTEL.
                BƯỚC 4: Đưa ra 3 kịch bản dự báo cho Quý tiếp theo.

                Trình bày:
                **Dữ liệu lịch sử (từ SQL):**
                | Tháng | Doanh thu | Units | Tăng trưởng so với tháng trước |
                |---|---|---|---|

                **3 Kịch bản Dự báo cho Quý tới:**
                | Kịch bản | Mô tả | Doanh thu Dự kiến | Điều kiện kích hoạt |
                |---|---|---|---|
                | 🟢 Lạc quan | [Mô tả] | [X] tỷ VNĐ (+Y%) | [Nếu A + B xảy ra] |
                | 🟡 Cơ bản | [Mô tả] | [X] tỷ VNĐ (+Y%) | [Nếu hiện trạng duy trì] |
                | 🔴 Thận trọng | [Mô tả] | [X] tỷ VNĐ (-Y%) | [Nếu C + D xảy ra] |

                **Đề xuất**: "Cần chuẩn bị cho kịch bản [X] bằng cách [hành động cụ thể]."

                ## ⚔️ VII. Cạnh Tranh Chiến Lược & Benchmark Đối Đầu
                Bảng benchmarking đối thủ (từ research context) + phân tích Win/Loss.
                Xác định Gót chân Achilles + Flanking Strategy.

                ## 📱 VIII. Chiến Lược Nội Dung Truyền Thông THEO PHÂN KHÚC
                Trình bày 03 bộ nội dung AIDA từ Brand Strategist (context):
                - PHÂN KHÚC GEN Z 🎯: Đầy đủ 4 thành phần AIDA.
                - PHÂN KHÚC DOANH NHÂN 💼: Đầy đủ 4 thành phần AIDA.
                - PHÂN KHÚC PHỔ THÔNG 👨‍👩‍👧‍👦: Đầy đủ 4 thành phần AIDA.

                ⚠️ YÊU CẦU: KHÔNG copy 1 câu slogan. Mỗi AIDA component ≥ 3 câu.

                ## 🗺️ IX. Lộ Trình Triển Khai 7 Ngày (Implementation Roadmap)
                Bảng kế hoạch PHÂN CHIA theo phân khúc:
                | Ngày | Hành Động | Phân khúc | Kênh | KPI | Ngân Sách | Khu Vực |
                Rules:
                - Mỗi ngày có KPI đo lường cụ thể riêng cho từng phân khúc.
                - Ngày 7 là "Review & Optimize" — tổng KPI đạt/chưa đạt.

                ## ⚠️ X. Quản Trị Rủi Ro & Điểm Kiểm Soát (Risk Management)
                ⚠️ KHÔNG ĐƯỢC viết rủi ro chung chung.
                ≥3 rủi ro, mỗi rủi ro có: Trigger, Xác suất, Impact, Contingency, Early Warning.

                ⚠️ YÊU CẦU QUY CHUẨN TOÀN BÁO CÁO:
                - Tiếng Việt 100% chuẩn mực văn phong quản trị cấp cao.
                - Toàn bộ báo cáo ≥ 2000 từ.
                - Tiền tệ: Luôn format 48,000,000,000 VNĐ (có dấu phẩy phân cách nghìn).
            """),
            expected_output=dedent(f"""
                # BÁO CÁO CHIẾN LƯỢC EXECUTIVE EXCELLENCE — [Ngày]

                ## 🔭 I. Tổng Quan Chiến Lược & Phân Tích Đa Chiều
                [Đoạn mở đầu 3 câu: Vị thế → Mâu thuẫn → Chủ đề chiến lược]
                **Q1/Q2/Q3:** [Trả lời với số liệu cụ thể]

                ---
                ## 📊 II. Phân Tích Hiệu Quả Tài Chính & Tối Ưu Hóa Nguồn Lực
                [Bảng ROI/CPA + Ma trận ROI × Budget + Đề xuất tái cấu trúc]

                ---
                ## 🏆 III. Toàn Cảnh Doanh Thu & BCG Matrix
                [Bảng doanh thu với model_name chính xác + BCG + Gap Analysis]

                ---
                ## 🔍 IV. Ma Trận SWOT
                [Bảng SWOT 2×2 + Chiến lược giao cắt SO/WO/ST/WT]

                ---
                ## 🌍 V. Phân Tích PESTEL
                [Bảng 6 yếu tố P-E-S-T-E-L + Impact + Hành động ứng phó]

                ---
                ## 📈 VI. Dự Báo Xu Hướng (Forecasting)
                [Bảng lịch sử + 3 kịch bản Lạc quan/Cơ bản/Thận trọng]

                ---
                ## ⚔️ VII. Cạnh Tranh Chiến Lược & Benchmark Đối Đầu
                [Bảng Head-to-Head + Gót chân Achilles + Flanking Strategy]

                ---
                ## 📱 VIII. Chiến Lược Nội Dung Theo Phân Khúc
                ### 🎯 Gen Z | 💼 Doanh nhân | 👨‍👩‍👧‍👦 Phổ thông
                [3 bộ AIDA riêng biệt]

                ---
                ## 🗺️ IX. Lộ Trình Triển Khai 7 Ngày
                [Bảng kế hoạch phân chia theo phân khúc + kênh + KPI]

                ---
                ## ⚠️ X. Quản Trị Rủi Ro & Điểm Kiểm Soát
                [≥3 rủi ro: Trigger + Xác suất + Impact + Contingency + Early Warning]
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

                📐 PHƯƠNG PHÁP SUY LUẬN (Chain-of-Thought):
                BƯỚC 1: Đọc lại báo cáo → Xác định 3 insight quan trọng nhất.
                BƯỚC 2: Phân loại mỗi insight vào 1 trong 3 loại signal.
                BƯỚC 3: Gọi tool signal_update 3 lần với nội dung trích xuất.

                HÀNH ĐỘNG CỤ THỂ — Gọi công cụ `signal_update` ÍT NHẤT 3 LẦN:

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

    def qa_task(self, agent, report_content: str, data_fetch_output: str) -> Task:
        return Task(
            description=dedent(f"""
                NHIỆM VỤ: Kiểm duyệt Báo cáo Chiến lược (LLM-as-a-Judge)
                
                Dưới đây là BÁO CÁO CẦN DUYỆT:
                ---
                {report_content}
                ---
                
                Dưới đây là DỮ LIỆU GỐC (SQL RAW DATA):
                ---
                {data_fetch_output}
                ---

                Hãy đóng vai trò là một Quality Assurance Agent cực kỳ khắt khe.

                📐 PHƯƠNG PHÁP KIỂM DUYỆT (Chain-of-Thought):
                BƯỚC 1: Quét toàn bộ báo cáo tìm ký tự CJK (Trung/Nhật/Hàn).
                BƯỚC 2: Kiểm tra mọi bảng dữ liệu — có dùng model_name chính xác không?
                BƯỚC 3: Đối chiếu số liệu trong báo cáo với DỮ LIỆU GỐC — tìm hallucination.
                BƯỚC 4: Kiểm tra cấu trúc đầy đủ — có đủ 10 phần không?

                CHECKLIST BẮT BUỘC:
                ☐ Không có ký tự CJK nào?
                ☐ Tất cả bảng dùng model_name chính xác từ SQL?
                ☐ Số liệu khớp với DỮ LIỆU GỐC?
                ☐ Có Ma trận SWOT đầy đủ 4 ô (S/W/O/T)?
                ☐ Có Phân tích PESTEL (≥4/6 yếu tố)?
                ☐ Có BCG Matrix?
                ☐ Có Forecasting (≥3 kịch bản)?
                ☐ Có nội dung phân khúc theo 3 nhóm (Gen Z/Doanh nhân/Phổ thông)?
                ☐ Có ≥3 rủi ro cụ thể với Trigger + Contingency?
                ☐ ≥2000 từ?

                Nếu BÁO CÁO có lỗi, hãy liệt kê chi tiết (Critique) những điểm cần sửa.
                Nếu BÁO CÁO hoàn hảo (pass tất cả checklist), trả về CHÍNH XÁC chuỗi: "PASSED".
            """),
            expected_output="Danh sách các lỗi (Critique) CẦN SỬA, hoặc trả về 'PASSED' nếu báo cáo đạt chuẩn.",
            agent=agent,
        )

    def refine_report_task(self, agent, original_report: str, critique: str) -> Task:
        return Task(
            description=dedent(f"""
                NHIỆM VỤ: Refine & Chỉnh sửa Báo cáo dựa trên phản hồi của QA (Reflection Pattern)
                
                BÁO CÁO CŨ CỦA BẠN:
                ---
                {original_report}
                ---
                
                PHẢN HỒI QA (CRITIQUE):
                ---
                {critique}
                ---

                📐 PHƯƠNG PHÁP SUY LUẬN (Chain-of-Thought):
                BƯỚC 1: Đọc PHẢN HỒI QA → Liệt kê TẤT CẢ các lỗi được chỉ ra.
                BƯỚC 2: Với MỖI lỗi, xác định vị trí chính xác trong báo cáo.
                BƯỚC 3: Sửa từng lỗi một — đảm bảo không tạo lỗi mới.
                BƯỚC 4: Đọc lại toàn bộ báo cáo sau khi sửa — kiểm tra tự xác nhận.

                Hãy sửa lại BÁO CÁO CŨ một cách triệt để dựa trên PHẢN HỒI QA.
                Tuyệt đối không để lại các lỗi đã được chỉ ra. Giữ nguyên cấu trúc 10 phần,
                chỉ sửa các lỗi vi phạm. Đảm bảo các framework mới (SWOT, PESTEL, Forecasting)
                có mặt đầy đủ trong báo cáo sau khi sửa.
            """),
            expected_output="Báo cáo hoàn chỉnh 10 phần, 100% tiếng Việt thuần khiết, dữ liệu chuẩn xác, đầy đủ SWOT/PESTEL/Forecasting, không còn lỗi QA.",
            agent=agent,
        )
