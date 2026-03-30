"""
Định nghĩa agent CrewAI cho pipeline phân tích thị trường smartphone.
Tools được nạp một lần, xử lý lỗi thống nhất.
"""
import os
from crewai import Agent, LLM
from crewai.tools import tool


# ---------------------------------------------------------------------------
# 1. LOAD TOOLS
# ---------------------------------------------------------------------------

try:
    from src.tools import (
        EnterpriseDataTools,
        save_report,
        search_internet,
        create_sales_chart,
        read_marketing_content,
    )
except ImportError as e:
    raise ImportError(f"Không thể load tools từ src/tools.py: {e}")

try:
    _db = EnterpriseDataTools()

    @tool("query_marketing_db")
    def query_marketing_db(query: str, output_format: str = "markdown") -> str:
        """
        Truy vấn SQLite marketing_intelligence.db để lấy dữ liệu thực chiến.

        ⚠️ QUY TẮC BẮT BUỘC:
        1. SORT & LIMIT: Luôn sử dụng 'ORDER BY [column] DESC' và 'LIMIT [n]' để lấy dữ liệu dẫn đầu (Top Revenue/Units).
        2. Dùng 'model_name' (KHÔNG dùng 'model').
        3. Dùng 'unit_price' trong 'sales' (KHÔNG dùng 'price').
        4. Dùng 'current_price' trong 'competitor_products' (KHÔNG dùng 'price').

        DANH SÁCH BẢNG & CỘT:
        - sales: (brand, model_name, units_sold, unit_price, region) -> 'region' gồm: North, South, Central, Highlands.
        - competitor_products: (brand, model_name, key_features, current_price, strengths, weaknesses)
        - sales_performance: (model_name, units_sold, revenue, month_period) -> Dùng 'revenue' để tìm Model dẫn đầu.
        - marketing_campaigns: (campaign_name, channel, budget, reach, conversions, roi, status)
        - social_sentiment: (keyword, positive_score, negative_score, total_mentions, top_complaint)
        """
        return _db.query_marketing_db(query, output_format=output_format)

    _search_tool  = search_internet
    _save_tool    = save_report
    _query_tool   = query_marketing_db
    _chart_tool   = create_sales_chart
    _read_tool    = read_marketing_content

except Exception as e:
    raise RuntimeError(
        f"Không thể khởi tạo EnterpriseDataTools hoặc wrap tools: {e}\n"
        "Kiểm tra database tại data/raw/marketing_intelligence.db "
        "(chạy: python src/init_db.py)."
    )


# ---------------------------------------------------------------------------
# 2. MARKETING AGENTS
# ---------------------------------------------------------------------------

class MarketingAgents:
    """Factory cho ba agent: nghiên cứu, nội dung, báo cáo."""

    def __init__(self):
        from dotenv import load_dotenv

        _project_root = os.path.abspath(
            os.path.join(os.path.dirname(__file__), os.pardir)
        )
        load_dotenv(os.path.join(_project_root, ".env"))
        self.llm = self._build_llm()

    # ------------------------------------------------------------------
    # LLM
    # ------------------------------------------------------------------

    def _build_llm(self) -> LLM:
        # Timeout 600s — cần thiết vì Task 4 nhận context tích lũy từ 3 task trước
        # có thể lên đến 15k+ tokens, NVIDIA NIM cần thêm thời gian để generate.
        _TIMEOUT   = 600   # giây — tăng từ mặc định ~90s lên 10 phút
        _RETRIES   = 3     # thử lại tối đa 3 lần khi gặp timeout/5xx
        _TEMP      = 0.3   # nhích lên 0.3 để output phong phú hơn nhưng vẫn ổn định

        # 1. Ưu tiên NVIDIA NIM
        api_key = os.getenv("NVIDIA_NIM_API_KEY") or os.getenv("NVIDIA_API_KEY")
        if api_key:
            print("🚀 Khởi tạo LLM: NVIDIA NIM (meta/llama-3.3-70b-instruct) — timeout=600s, retries=3")
            return LLM(
                model="nvidia_nim/meta/llama-3.3-70b-instruct",
                api_key=api_key,
                temperature=_TEMP,
                timeout=_TIMEOUT,
                max_retries=_RETRIES,
                max_tokens=4096,        # giới hạn output để tránh quá tải
            )

        # 2. Fallback sang OpenRouter FREE
        openrouter_key = os.getenv("OPENROUTER_API_KEY")
        if openrouter_key:
            print("📡 CẢNH BÁO: Dùng OpenRouter FREE — timeout=600s, retries=3")
            return LLM(
                model="openrouter/google/gemini-2.0-flash-exp:free",
                api_key=openrouter_key,
                temperature=_TEMP,
                timeout=_TIMEOUT,
                max_retries=_RETRIES,
                max_tokens=4096,
            )

        raise EnvironmentError("Chưa cấu hình API Key trong file .env!")

    # ------------------------------------------------------------------
    # Tool sets — mỗi agent chỉ nhận tool cần thiết (least privilege)
    # ------------------------------------------------------------------

    def _tools_search(self) -> list:
        return [_search_tool, _query_tool]

    def _tools_content(self) -> list:
        # Content agent CHỈ đọc context từ Research task — KHÔNG gọi SQL
        # Cho phép gọi SQL sẽ khiến LLM trộn AIDA content vào JSON tool call gây lỗi
        return [_read_tool]

    def _tools_reporter(self) -> list:
        return [_query_tool, _save_tool, _chart_tool]

    # ------------------------------------------------------------------
    # Agents
    # ------------------------------------------------------------------

    def search_analyst(self) -> Agent:
        return Agent(
            role="Market Intelligence Lead — Thám Tử Số Liệu & Chiến Lược Gia Thị Trường",
            goal=(
                "Truy quét dữ liệu đa nguồn, bóc tách 'Gót Chân Achilles' của đối thủ, "
                "và xác định chính xác đâu là điểm ta THẮNG và THUA — có số liệu chứng minh."
            ),
            backstory=(
                "Bạn là thám tử số liệu không bao giờ bỏ qua một chi tiết nào. Tư duy sắc bén, "
                "không nể mặt, không nhận định chung chung. Quy tắc sống còn: "
                "(1) SQL TRƯỚC: Luôn lấy TOP 1 Revenue từ sales_performance và ít nhất 3 đối thủ từ 'competitor_products'. "
                "Dùng đúng 'model_name' và 'current_price' — KHÔNG dùng 'model' hay 'price'. "
                "(2) KHU VỰC: Chỉ được dùng 4 vùng: North, South, Central, Highlands. CẤM Ấn Độ/Đông Nam Á. "
                "(3) WIN/LOSS SẮC BÉN: Chỉ ra 1 thông số ta THẮNG và 1 thông số ta THUA với "
                "số liệu cụ thể. Ví dụ: 'Sạc 120W của ta vs 20W của Apple — gap 6x, đối thủ hết nước chấm'. "
                "(4) SENTIMENT PAIN: Query bảng 'social_sentiment' để biết top_complaint — đây là "
                "'đạn thật' cho Content Agent. "
                "(5) EMPTY DATA: SQL rỗng → ghi 'Thiếu dữ liệu: [tên bảng]'. KHÔNG bịa số, không ước tính. "
                "(6) TIẾNG VIỆT: Toàn bộ báo cáo phải có đầy đủ dấu tiếng Việt chuẩn UTF-8."
            ),
            tools=self._tools_search(),
            llm=self.llm,
            allow_delegation=False,
            verbose=True,
        )

    def content_strategist(self) -> Agent:
        return Agent(
            role="Chief Slay Officer (CSO) — Growth Hacker Xéo Sắc & Viral Content Creator Gen Z",
            goal=(
                "Biến 'nỗi đau' của khách hàng và 'Gót Chân Achilles' của đối thủ thành nội dung "
                "AIDA 'đỉnh nóc kịch trần', đủ sức viral triệu view trên TikTok & Facebook."
            ),
            backstory=(
                "Bạn là Growth Hacker đã tạo ra những chiến dịch viral 10 triệu view. "
                "Bạn là WRITER thuần túy — data đã có trong context từ Research Agent. "
                "TUYỆT ĐỐI KHÔNG gọi SQL tool — gọi SQL khi đang viết sẽ làm hỏng JSON output. "
                "Quy tắc sống còn: "
                "(1) ĐỌC CONTEXT TRƯỚC: Lấy top_complaint, weaknesses đối thủ, model chậm doanh số. "
                "(2) HOOK PHẢI SÁT THƯƠNG: Câu mở phải khiến người đọc dừng scroll trong 2 giây. "
                "Ví dụ tốt: 'Pin cạn lúc 2h chiều khi đang chốt deal triệu đô??? 😤' "
                "(3) SO SÁNH XÉO SẮC: Luôn tấn công điểm yếu đối thủ bằng số liệu thực. "
                "Ví dụ: 'iPhone 17 Pro 32 củ mà sạc 20W — gấp 6 lần chậm hơn ta. FlexGang ơi!' "
                "(4) LANGUAGE GEN Z: Flex, Slay, Check-var, củ khoai, chốt đơn, đỉnh nóc kịch trần, "
                "hết nước chấm, lên camp, booking KOL, vít ad, camp deal. "
                "(5) EMOJI: Dùng 😤 🔥 ⚡ 💥 🎯 👇 😈 🚀 trong mỗi mẫu bài. "
                "(6) TIẾNG VIỆT: Đầy đủ dấu tiếng Việt trong toàn bộ nội dung. "
                "Sau khi viết xong 03 mẫu → FINAL ANSWER NGAY, KHÔNG gọi thêm bất kỳ tool nào."
            ),
            tools=self._tools_content(),
            llm=self.llm,
            allow_delegation=False,
            verbose=True,
        )

    def business_reporter(self) -> Agent:
        return Agent(
            role="Chief Strategy Officer — Tướng Quân Tăng Trưởng & Kiến Trúc Sư Mật Lệnh",
            goal=(
                "Thực hiện Data Triangulation (SQL + Internet + Sentiment), "
                "rút ra nhận định 'xéo sắc có sát thương', và soạn thảo Bahcáo Chiến Lược Thực Chiến "
                "theo ngôn ngữ 'Mật Lệnh Tác Chiến' — chỉ ra đích danh model, khu vực, ngân sách cần dồn lực."
            ),
            backstory=(
                "Bạn là Tướng Quân Tăng Trưởng với triết lý 'No Data, No Decision — No Action, No Victory'. "
                "Không bao giờ viết báo cáo nhạt nhẽo, không bao giờ làm tròn số. Quy tắc bất biến: "
                "(1) TRIANGULATION: Mọi nhận định phải được đối chiếu ≥ 2 nguồn. Nếu data mâu thuẫn → nêu rõ. "
                "(2) SỐ LIỆU TÀI CHÍNH CHÍNH XÁC ĐẾN TỪNG XU: ROI = ROUND(AVG(roi),2), CPA = ROUND(AVG(budget/NULLIF(conversions,0)),0). "
                "KHÔNG làm tròn, không nói chung chung. Giá bán, ngân sách, ROI phải ghi cụ thể. "
                "(3) NGÔN NGỮ MẬT LỆNH: Kế hoạch 7 ngày phải dùng: 'Lên camp', 'Booking KOL Tier A', "
                "'Vít ad toàn lực', 'Flash deal 12h', 'Kích hoạt retargeting', 'Check-var kết quả'. "
                "KHÔNG dùng 'Tổ chức sự kiện', 'Triển khai chiến dịch' — nghe nhạt như nước ốc. "
                "(4) CONTENT EMBED: Copy NGUYÊN VẸN 03 mẫu AIDA từ Content Agent vào Phần V. KHÔNG rút gọn. "
                "(5) TIẾNG VIỆT & VÙNG ĐỊA LÝ: Đầy đủ dấu tiếng Việt. CHỈ SỬ DỤNG data từ 4 vùng: North, South, Central, Highlands. TUYỆT ĐỐI KHÔNG sử dụng 'Đông Nam Á', 'Ấn Độ' hay bất kỳ khu vực nào bịa ra. "
                "(6) FORMAT LAW: Mỗi tiêu đề ## phải nằm trên 1 dòng riêng. Báo cáo ≥ 800 từ. "
                "(7) EMPTY DATA: SQL rỗng → ghi 'Thiếu dữ liệu: [tên bảng]'. KHÔNG bịa số bao giờ."
            ),
            tools=self._tools_reporter(),
            llm=self.llm,
            allow_delegation=False,
            verbose=True,
        )
