"""
MarketingTasks — Pipeline 4 stages theo chuẩn Data Triangulation.

QUYỀN LỢI ĐÃ ĐƯỢC ĐẢM BẢO:
  ✅ Chỉ dùng 4 khu vực thực tế từ DB: North, South, Central, Highlands
  ✅ Giá lấy từ 'current_price' trong competitor_products (KHÔNG bịa)
  ✅ ROI logic đúng chiều: cao + budget thấp → tăng; thấp + budget cao → cắt
  ✅ Định dạng số lớn: 48,000,000,000 VNĐ (không viết 48000000000)
  ✅ Tiếng Việt đầy đủ dấu UTF-8 trong toàn bộ output
  ✅ Persona "Chief Slay Officer" — Flex, Slay, Check-var, Đỉnh nóc kịch trần

Pipeline 4 stages:
  Stage 1  : Tình báo thị trường & Benchmarking đối thủ
  Stage 2  : Sáng tạo nội dung Gen Z (AIDA Format)
  Stage 2.5: Pre-fetch SQL tài chính (giảm token cho Stage 3)
  Stage 3  : Báo cáo Chiến lược Thực chiến (Executive Report)
"""
from typing import List
from textwrap import dedent

try:
    from crewai import Task
    from crewai.tools import BaseTool
except ImportError as e:
    raise ImportError(f"Không thể import CrewAI: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# GROUND TRUTH — Dữ liệu cứng từ database, dùng làm anchor cho các prompt
# ─────────────────────────────────────────────────────────────────────────────
_REGIONS = "North, South, Central, Highlands"
_ROI_DATA = "TikTok=1383.21 (budget 235tr), Instagram=995.0 (budget 28tr), Facebook=980.42 (budget 166tr), KOL=951.66, YouTube=333.57 (budget 461tr), Google Search=332.98 (budget 468tr)"
_REGION_NOTE = f"⚠️ CHỈ DÙNG 4 KHU VỰC NÀY: {_REGIONS}. KHÔNG dùng 'Đông Nam Á', 'Ấn Độ', 'Châu Âu' hay bất kỳ khu vực nào khác."


class MarketingTasks:

    # ══════════════════════════════════════════════════════════════════════════
    # STAGE 1 — THU THẬP TÌNH BÁO THỊ TRƯỜNG & BENCHMARKING ĐỐI THỦ
    # ══════════════════════════════════════════════════════════════════════════

    def research_task(self, agent, market_topic: str) -> Task:
        return Task(
            description=dedent(f"""
                NHIỆM VỤ: Tình báo thị trường — {market_topic}

                {_REGION_NOTE}

                BƯỚC 1 — BENCHMARKING ĐỐI THỦ (Bắt buộc SQL, ≥ 3 đối thủ):
                    SELECT brand, model_name, key_features, current_price,
                           strengths, weaknesses
                    FROM competitor_products
                    ORDER BY current_price DESC
                    LIMIT 6

                Xuất bảng: | Đối Thủ | Model | Tính Năng | Giá (VNĐ) | Điểm Mạnh | Gót Chân Achilles |
                Lưu ý format giá: 32,000,000 VNĐ (thêm dấu phẩy phân cách hàng nghìn).

                BƯỚC 1.5 — MODEL DẪN ĐẦU DOANH THU (Bắt buộc SQL):
                    SELECT model_name, SUM(units_sold * unit_price) AS revenue
                    FROM sales
                    GROUP BY model_name
                    ORDER BY revenue DESC
                    LIMIT 1

                BƯỚC 2 — PHÂN TÍCH WIN/LOSS (Bắt buộc, dùng data từ SQL):
                - ✅ 1 thông số Ta THẮNG rõ ràng: nêu số liệu CỦA TA vs ĐỐI THỦ.
                - ❌ 1 thông số Ta THUA thực sự: không che giấu, nêu lý do khách quan.

                BƯỚC 3 — MODEL DOANH SỐ THẤP NHẤT (Bắt buộc SQL):
                    SELECT model_name, region, SUM(units_sold) AS total_units,
                           ROUND(AVG(unit_price), 0) AS avg_price
                    FROM sales
                    GROUP BY model_name, region
                    ORDER BY total_units ASC
                    LIMIT 2

                {_REGION_NOTE}
                Chỉ liệt kê các khu vực có trong kết quả SQL. KHÔNG thêm khu vực ngoài.

                BƯỚC 4 — NỖI ĐAU KHÁCH HÀNG — Social Sentiment (Bắt buộc SQL):
                    SELECT keyword, top_complaint, negative_score,
                           total_mentions, trending_platform
                    FROM social_sentiment
                    ORDER BY negative_score DESC
                    LIMIT 3

                BƯỚC 5 — XU HƯỚNG GEN Z:
                Tìm 3 buzzword/trend Gen Z đang HOT nhất trên TikTok VN qua search tool.

                ⚠️ QUY TẮC SQL TUYỆT ĐỐI:
                - Dùng 'model_name' (KHÔNG dùng 'model')
                - Dùng 'unit_price' (KHÔNG dùng 'price')
                - Dùng 'current_price' trong competitor_products (KHÔNG dùng 'price')
                - SQL rỗng → ghi 'Thiếu dữ liệu: [tên bảng]'. KHÔNG bịa số.
                - Số > 1 triệu → format: 32,000,000 VNĐ (có dấu phẩy).
                - KHU VỰC: KHÔNG ĐƯỢC dùng Ấn Độ hay Đông Nam Á. Chỉ dùng North, South, Central, Highlands.
            """),
            expected_output=dedent("""
                ## 🕵️ I. Bảng Benchmarking Đối Thủ
                | Đối Thủ | Model | Tính Năng Nổi Bật | Giá (VNĐ) | Điểm Mạnh | Gót Chân Achilles |
                (≥ 3 đối thủ, giá format 32,000,000 VNĐ)

                ## 💰 II. Model Dẫn Đầu Doanh Thu (Top 1 Revenue)
                *Model: [model_name] | Doanh thu: [revenue] VNĐ*

                ## ⚔️ III. Phân Tích WIN/LOSS
                - ✅ Ta THẮNG: [tính năng] — [số liệu Ta] vs [số liệu Đối Thủ]
                - ❌ Ta THUA: [tính năng] — [lý do + dữ liệu thực]

                ## 📉 IV. Top 5 Model Doanh Số Thấp Nhất
                | model_name | region | total_units | avg_price |
                (Chỉ dùng khu vực: North/South/Central/Highlands)

                ## 😤 V. Nỗi Đau Khách Hàng
                | keyword | top_complaint | negative_score | trending_platform |

                ## 🔥 VI. 3 Buzzwords Gen Z Đang Trending
            """),
            agent=agent,
        )

    # ══════════════════════════════════════════════════════════════════════════
    # STAGE 2 — SÁNG TẠO NỘI DUNG GEN Z (AIDA FORMAT)
    # ══════════════════════════════════════════════════════════════════════════

    def content_creation_task(self, agent, research_task: Task) -> Task:
        return Task(
            description=dedent("""
                NHIỆM VỤ: Đóng vai Chief Slay Officer — tạo 03 mẫu bài đăng VIRAL chuẩn AIDA.

                DỮ LIỆU ĐẦU VÀO: Đọc TRỰC TIẾP từ context của Research Agent.
                Lấy từ context:
                - top_complaint (nỗi đau thực tế, ví dụ: "Pin yếu", "Sạc chậm", "Giá cao")
                - Gót Chân Achilles của đối thủ (từ bảng weaknesses trong benchmarking)
                - Model đang doanh số thấp nhất (model_name cụ thể từ SQL)
                - key_features và current_price của sản phẩm (LẤY GIÁ TỪ SQL, KHÔNG bịa)

                TUYỆT ĐỐI KHÔNG GỌI SQL TOOL. Dữ liệu đã có trong context. Viết Final Answer ngay.

                ════════════════════════════════════════════════
                MẪU 1 — 💥 Pain Point Attack
                ════════════════════════════════════════════════
                [HOOK]: Câu mở "sát thương cao" dựa trên top_complaint THỰC TẾ từ context.
                  Bắt buộc dùng emoji + ngôn ngữ Gen Z.
                  Ví dụ HAY: "📱 Pin cạn lúc 2h chiều khi đang chốt deal 50 triệu??? Bro ơi Check-var cái này 😤"
                  Ví dụ DỞ (KHÔNG làm): "Sản phẩm của chúng tôi rất tốt." ← bị loại ngay

                [BODY]: So sánh XÉO SẮC với đối thủ — dùng GIÁ THỰC TẾ từ current_price.
                  Format bắt buộc:
                  "❌ [Đối thủ] [giá thực từ SQL]VNĐ mà [điểm yếu thực tế từ weaknesses]"
                  "✅ Ta [giá thực từ SQL] VNĐ mà [tính năng vượt trội cụ thể]"
                  Ví dụ: "❌ iPhone 17 Pro 32,000,000 VNĐ mà sạc 20W — rùa bò 2026 🐢"
                          "✅ Mi 16 Pro 19,000,000 VNĐ, sạc 120W — đầy pin trong 30 phút ⚡"

                [DESIRE]: Tính năng của ta giải quyết nỗi đau như thế nào — cụ thể, có số liệu.
                  Dùng style storytelling ngắn: "Hãy tưởng tượng bạn vừa kết thúc 3h livestream..."

                [CTA]: Kêu gọi hành động quyết liệt với urgency.
                  Dùng: "Check-var ngay 👇", "Chốt đơn kẻo hết ⚡", "Slay cùng [tên model] hôm nay".

                [HASHTAGS]: Đúng 10 hashtags. Bắt buộc có: tên model + pain point keyword + Gen Z slang.

                ════════════════════════════════════════════════
                MẪU 2 — 💪 Flexing Mode (Khoe cấu hình Model Dẫn Đầu Doanh Thu)
                ════════════════════════════════════════════════
                [HOOK]: Câu mở Flex về Model đang DẪN ĐẦU DOANH THU (lấy từ Top 1 Revenue trong context Research).
                  BẮT BUỘC NÊU ĐÍCH DANH MODEL (vd: Find X9 Pro) và GIÁ THỰC TẾ (current_price).
                  Ví dụ: "⚡ Snapdragon 8 Gen 5 + Camera Hasselblad mà [Tên model dẫn đầu] giá chỉ [current_price] VNĐ??? Flex hard 🔥"

                [BODY]: Đúng 3 tính năng "đỉnh nóc kịch trần" của model dẫn đầu — mỗi tính năng theo format:
                  "⚡ [Tính năng]: [Thông số Ta] vs [Thông số Đối Thủ] — [Nhận định xéo sắc]"

                [DESIRE]: Mini story 2-3 câu về trải nghiệm người dùng thực tế, sống động.
                  Ví dụ: "Check-var anh kỹ sư dùng Mi 16 Pro cả ngày làm việc nặng, 6h tối vẫn còn 45% pin."

                [CTA]: Hành động cụ thể + deadline tạo FOMO.
                [HASHTAGS]: Đúng 10 hashtags trending.

                ════════════════════════════════════════════════
                MẪU 3 — 🔥 Deal Alert (Giải cứu model chậm KPI)
                ════════════════════════════════════════════════
                [HOOK]: Nêu ĐÍCH DANH model đang doanh số thấp nhất (từ context) + deal hấp dẫn.
                  GIÁ PHẢI LẤY TỪ context Research — KHÔNG bịa giá.
                  Ví dụ: "💥 [Tên model cụ thể] — deal cuối tháng XỊN NHẤT từ trước tới nay!"

                [BODY]: Deal/ưu đãi CỰC CỤ THỂ — giá thực, deadline rõ, số lượng giới hạn.
                  "Giá gốc: [current_price từ SQL] → Ưu đãi hôm nay: [giá deal] — tiết kiệm [số tiền]"

                [DESIRE]: Social proof thuyết phục: đơn đã chốt, review 5 sao.
                  Ví dụ: "1,247 người vừa chốt đơn trong 24h qua — bạn còn chần chừ gì?"

                [CTA]: CTA "căng như dây đàn": "Còn [X] suất — Bấm NGAY 👇 hoặc hối hận cả đời 😈"
                [HASHTAGS]: Đúng 10 hashtags có tên model + deal keyword.

                ════════════════════════════════════════════════
                QUY TẮC VĂN PHONG TUYỆT ĐỐI:
                ════════════════════════════════════════════════
                ✅ PHẢI dùng: Flex, Slay, Check-var, củ khoai, chốt đơn, đỉnh nóc kịch trần,
                   hết nước chấm, gót chân Achilles, lên camp, booking KOL, vít ad
                ✅ PHẢI dùng Emoji (😤, 🔥, ⚡, 💥, 🎯, 👇, 😈, 🚀, 🎪, 💪)
                ✅ PHẢI có đầy đủ dấu tiếng Việt trong toàn bộ nội dung
                ✅ GIÁ THỰC TẾ: 32,000,000 VNĐ (có dấu phẩy) — KHÔNG viết "32 triệu" chung chung
                ❌ KHÔNG gọi SQL tool — VIẾT FINAL ANSWER NGAY sau khi xong 03 mẫu
                ❌ KHÔNG dùng "Quý khách", "Sản phẩm ưu việt", "Đội ngũ chuyên nghiệp"
                ❌ KHÔNG bịa giá — chỉ dùng giá từ context Research
            """),
            expected_output=dedent("""
                ## 💥 MẪU 1 — Pain Point Attack
                **[HOOK]**: ... (1 câu, có emoji, dựa trên top_complaint thực tế)
                **[BODY]**: ... (so sánh giá thực ❌đối thủ vs ✅ta, có số liệu)
                **[DESIRE]**: ... (giải quyết nỗi đau, có storytelling)
                **[CTA]**: ... (kêu gọi quyết liệt với urgency)
                **[HASHTAGS]**: #Tag1 #Tag2 ... (đúng 10 tags)

                ---

                ## 💪 MẪU 2 — Flexing Mode
                **[HOOK]**: ...
                **[BODY]**: (3 tính năng theo format ⚡ [TT]: [Số ta] vs [Số đối thủ] — [nhận định])
                **[DESIRE]**: ...
                **[CTA]**: ...
                **[HASHTAGS]**: #Tag1 #Tag2 ... (đúng 10 tags)

                ---

                ## 🔥 MẪU 3 — Deal Alert
                **[HOOK]**: ... (nêu đích danh model, giá thực từ SQL)
                **[BODY]**: ... (giá gốc → giá deal, deadline, số lượng)
                **[DESIRE]**: ... (social proof với số cụ thể)
                **[CTA]**: ... (countdown urgency)
                **[HASHTAGS]**: #Tag1 #Tag2 ... (đúng 10 tags)
            """),
            agent=agent,
            context=[research_task],
        )

    # ══════════════════════════════════════════════════════════════════════════
    # STAGE 2.5 — PRE-FETCH SQL TÀI CHÍNH (Giảm tải Token cho Stage 3)
    # ══════════════════════════════════════════════════════════════════════════

    def data_fetch_task(self, agent, research_task: Task, content_task: Task) -> Task:
        return Task(
            description=dedent(f"""
                NHIỆM VỤ DUY NHẤT: Chạy đúng 3 câu SQL sau và trả về kết quả thô.
                KHÔNG phân tích. KHÔNG thêm nhận xét. Chỉ lấy dữ liệu thô.

                {_REGION_NOTE}

                SQL 1 — ROI & CPA theo kênh marketing:
                    SELECT channel,
                           ROUND(AVG(roi), 2) AS avg_roi,
                           ROUND(AVG(budget * 1.0 / NULLIF(conversions, 0)), 0) AS avg_cpa,
                           SUM(budget) AS total_budget
                    FROM marketing_campaigns
                    GROUP BY channel
                    ORDER BY avg_roi DESC

                SQL 2 — Doanh thu chi tiết theo sản phẩm:
                    SELECT model_name, SUM(units_sold) AS units_sold, SUM(units_sold * unit_price) AS revenue
                    FROM sales
                    GROUP BY model_name
                    ORDER BY revenue DESC
                    LIMIT 10

                SQL 3 — Doanh thu theo khu vực địa lý
                (Khu vực thực tế trong DB: {_REGIONS}):
                    SELECT region,
                           SUM(units_sold) AS total_units,
                           ROUND(SUM(units_sold * unit_price), 0) AS total_revenue
                    FROM sales
                    GROUP BY region
                    ORDER BY total_revenue DESC

                Trả về đúng nguyên định dạng bảng Markdown. KHÔNG tóm tắt. KHÔNG diễn giải.
            """),
            expected_output=(
                "3 bảng Markdown chứa kết quả thô từ SQL:\n"
                f"Bảng 1: channel | avg_roi | avg_cpa | total_budget (kênh: TikTok/Instagram/Facebook/YouTube/Google Search/KOL)\n"
                f"Bảng 2: model_name | units_sold | revenue\n"
                f"Bảng 3: region | total_units | total_revenue (chỉ hiện: {_REGIONS})"
            ),
            agent=agent,
            context=[research_task, content_task],
        )

    # ══════════════════════════════════════════════════════════════════════════
    # STAGE 3 — BÁO CÁO CHIẾN LƯỢC THỰC CHIẾN (DATA TRIANGULATION)
    # ══════════════════════════════════════════════════════════════════════════

    def marketing_strategy_task(
        self, agent, research_task: Task, content_task: Task,
        data_fetch_task: Task, tools: List[BaseTool]
    ) -> Task:
        return Task(
            description=dedent(f"""
                NHIỆM VỤ: Viết Báo cáo Chiến lược Thực chiến — DATA TRIANGULATION.
                KHÔNG query SQL thêm. 100% dữ liệu đã có trong context từ 3 task trước.

                {_REGION_NOTE}

                ════════════════════════════════════════════════
                QUY TẮC DỮ LIỆU CỨNG (VI PHẠM = BÁO CÁO THẤT BẠI):
                ════════════════════════════════════════════════
                1. TOP 1 MODEL: Bạn PHẢI nhìn vào kết quả 'Model Dẫn Đầu Doanh Thu' từ context. Nếu SQL báo Find X9 Pro, báo cáo PHẢI nói về Find X9 Pro. KHÔNG ĐƯỢC bịa ra iPhone hay Xiaomi dẫn đầu nếu dữ liệu SQL không nói vậy.
                2. KHU VỰC: Chỉ được nhắc đến: {_REGIONS}
                   → TUYỆT ĐỐI KHÔNG viết "Đông Nam Á", "Ấn Độ", "Châu Âu", "Tây Bắc Bộ" hay bất kỳ KV nào khác.
                3. GIÁ SẢN PHẨM: Lấy từ current_price trong context cho model đó. Format: 32,000,000 VNĐ.
                4. REVENUE: Lấy từ kết quả SQL trong context — KHÔNG làm tròn thành "48 tỷ", viết đủ: 48,000,000,000 VNĐ.
                5. ROI ANALYSIS ĐÚNG CHIỀU (dùng data thực: {_ROI_DATA}):
                   - ROI CAO + budget THẤP → "Đang bị bỏ đói — double budget NGAY"
                   - ROI THẤP + budget CAO → "Đang burn tiền — cắt giảm 30% và tái phân bổ"
                   → KHÔNG được nhận định ngược chiều (ROI cao mà bảo burn tiền là SAI).
                ════════════════════════════════════════════════

                CẤU TRÚC BÁO CÁO — 7 PHẦN (≥ 800 từ)
                ════════════════════════════════════════════════

                ## 🔭 I. Tổng Quan Chiến Lược & Data Triangulation
                Nhận định "xéo sắc" từ đối chiếu 3 nguồn dữ liệu. Ít nhất 150 từ.
                Đặt 3 câu hỏi Data Triangulation và trả lời bằng data thực:
                - Kênh nào ROI cao nhất nhưng ngân sách đang "đói"? → Đề xuất cụ thể.
                - Model nào revenue thấp nhưng đối thủ mạnh ở segment đó? → Cơ hội tấn công.
                - Khu vực nào ({_REGIONS}) revenue thấp nhưng sentiment tốt? → Khai thác ngay.

                ## 📊 II. Hiệu Quả Tài Chính Chi Tiết
                Bảng ROI/CPA đầy đủ từ context. KHÔNG làm tròn số (1383.21, không phải 1383).
                Nhận định theo logic kinh tế ĐÚNG CHIỀU:
                - TikTok ROI=1383.21, budget 235tr → "UNDERINVESTED — double budget ngay"
                - Google Search ROI=332.98, budget 468tr → "Đang burn 468,000,000 VNĐ/chu kỳ — cắt 30%"

                ## 🏆 III. Phân Tích Doanh Thu Theo Sản Phẩm & Khu Vực
                Bảng revenue từ context. Format số: 48,000,000,000 VNĐ.
                Khu vực: chỉ dùng {_REGIONS}. KHÔNG thêm khu vực khác.
                Chỉ ra:
                - LEAD: Model/khu vực nào dẫn đầu (dữ liệu SQL nói gì?)
                - LAG: Model/khu vực nào tụt hậu (lý do theo data)

                ## ⚔️ IV. Phân Tích Cạnh Tranh & Đòn Tấn Công
                Từ benchmarking Task 1:
                - ✅ Đòn mạnh nhất của Ta: [tính năng + số liệu cụ thể từ SQL]
                - ❌ Điểm yếu cần khắc phục: [tính năng + kế hoạch cụ thể]
                - 🎯 Cơ hội tấn công Gót Chân Achilles đối thủ nào with vũ khí gì?

                ## 📱 V. Kho Vũ Khí Truyền Thông (Nội Dung AIDA)
                PASTE NGUYÊN VẸN toàn bộ 03 mẫu bài đăng từ Task 2.
                KHÔNG rút gọn. KHÔNG tóm tắt. KHÔNG thay đổi từ ngữ.

                ## 🗺️ VI. Kế Hoạch Tác Chiến 7 Ngày — MẬT LỆNH
                Bảng 7 hàng — Format cứng:
                | Ngày | Mật Lệnh Hành Động | Kênh | Khu Vực | Ngân Sách (VNĐ) | KPI Kỳ Vọng | Lý Do Từ Data |

                Quy tắc:
                - Khu vực: chỉ chọn trong {_REGIONS}
                - Ngân sách: format 50,000,000 VNĐ (không viết 50tr)
                - Hành động: dùng "Lên camp TikTok", "Booking KOL Tier A", "Vít ad toàn lực",
                  "Flash deal 12h", "Kích hoạt retargeting", "Check-var kết quả A/B test"
                - KHÔNG dùng: "Tổ chức sự kiện", "Triển khai chiến dịch"

                ## ⚠️ VII. Rủi Ro & Điểm Kiểm Soát
                Ít nhất 3 rủi ro theo format:
                "⚠️ Rủi ro: [mô tả] → 📡 Dấu hiệu: [chỉ số cụ thể] → 🛡️ Countermeasure: [hành động]"

                ════════════════════════════════════════════════
                QUY TẮC TUYỆT ĐỐI:
                ════════════════════════════════════════════════
                - Tiếng Việt đầy đủ dấu trong TOÀN BỘ báo cáo (tiêu đề + nội dung + bảng).
                - Số tài chính: 48,000,000,000 VNĐ — KHÔNG làm tròn.
                - Báo cáo ≥ 800 từ, đủ 7 phần, mỗi ## trên 1 dòng riêng.
                - KHÔNG bịa số, KHÔNG bịa khu vực, KHÔNG nhận định ngược chiều data.
            """),
            expected_output=dedent(f"""
                BÁO CÁO CHIẾN LƯỢC THỰC CHIẾN (≥ 800 TỪ):

                ## 🔭 I. Tổng Quan Chiến Lược & Data Triangulation
                (≥ 150 từ, 3 câu hỏi triangulation có trả lời từ data)

                ## 📊 II. Hiệu Quả Tài Chính Chi Tiết
                (Bảng ROI/CPA không làm tròn + nhận định đúng chiều)
                TikTok ROI=1383.21 → UNDERINVESTED / Google Search ROI=332.98 → burn tiền

                ## 🏆 III. Phân Tích Doanh Thu Theo Sản Phẩm & Khu Vực
                (Bảng revenue format 48,000,000,000 VNĐ — khu vực: {_REGIONS} only)

                ## ⚔️ IV. Phân Tích Cạnh Tranh & Đòn Tấn Công
                (WIN/LOSS với giá current_price thực từ SQL)

                ## 📱 V. Kho Vũ Khí Truyền Thông
                (03 mẫu AIDA nguyên vẹn từ Task 2)

                ## 🗺️ VI. Kế Hoạch Tác Chiến 7 Ngày
                (Bảng 7 hàng — khu vực {_REGIONS} only, budget format VNĐ)

                ## ⚠️ VII. Rủi Ro & Điểm Kiểm Soát
                (≥ 3 rủi ro theo format ⚠️→📡→🛡️)
            """),
            agent=agent,
            context=[research_task, content_task, data_fetch_task],
            tools=tools,
        )
