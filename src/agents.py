"""
Định nghĩa Agent CrewAI cho pipeline phân tích thị trường smartphone.
Nâng cấp chuẩn Executive Excellence cho môi trường doanh nghiệp cao cấp.
"""
import os
from crewai import Agent, LLM
from crewai.tools import tool
from src.config import setup_logging, LLM_TIMEOUT, MAX_RETRIES

# Initialize logger
logger = setup_logging("marketing_agents")

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
        SignalUpdateTool,
    )
except ImportError as e:
    logger.critical(f"Không thể load tools từ src/tools.py: {e}")
    raise ImportError(f"Không thể load tools từ src/tools.py: {e}")

try:
    _db = EnterpriseDataTools()

    @tool("query_marketing_db")
    def query_marketing_db(query: str, output_format: str = "markdown") -> str:
        """
        Truy vấn SQLite marketing_intelligence.db để lấy dữ liệu thực chiến.
        
        ⚠️ QUY TẮC BẮT BUỘC:
        1. SORT & LIMIT: Luôn sử dụng 'ORDER BY [column] DESC' và 'LIMIT [n]'.
        2. CÀI ĐẶT TƯ DUY: Tìm Model dẫn đầu doanh thu qua SUM(units_sold*unit_price).
        3. Dùng 'model_name' (KHÔNG dùng 'model').
        4. Dùng 'unit_price' trong 'sales' (KHÔNG dùng 'price').
        5. Dùng 'current_price' trong 'competitor_products' (KHÔNG dùng 'price').
        """
        return _db.query_marketing_db(query, output_format=output_format)

    _search_tool  = search_internet
    _save_tool    = save_report
    _query_tool   = query_marketing_db
    _chart_tool   = create_sales_chart
    _read_tool    = read_marketing_content
    _signal_tool  = SignalUpdateTool()

except Exception as e:
    logger.critical(f"Lỗi khởi tạo EnterpriseDataTools: {e}")
    raise RuntimeError(f"Lỗi khởi tạo EnterpriseDataTools: {e}")


# ---------------------------------------------------------------------------
# 2. MARKETING AGENTS FACTORY
# ---------------------------------------------------------------------------

class MarketingAgents:
    """Factory cho các agent chiến lược: nghiên cứu, nội dung, báo cáo cấp cao."""

    def __init__(self):
        self.llm = self._build_llm()

    def _build_llm(self) -> LLM:
        """
        Khởi tạo LLM với cấu hình tối ưu và Error Resilience.
        """
        _TEMP = 0.3
        
        # 1. Ưu tiên NVIDIA NIM
        nvidia_key = os.getenv("NVIDIA_NIM_API_KEY") or os.getenv("NVIDIA_API_KEY")
        if nvidia_key:
            logger.info("🚀 Cấu hình LLM: NVIDIA NIM (Llama-3.3-70B)")
            return LLM(
                model="nvidia_nim/meta/llama-3.3-70b-instruct",
                api_key=nvidia_key,
                temperature=_TEMP,
                timeout=LLM_TIMEOUT,
                max_retries=MAX_RETRIES,
                max_tokens=4096,
            )

        # 2. Fallback sang OpenRouter
        openrouter_key = os.getenv("OPENROUTER_API_KEY")
        if openrouter_key:
            logger.warning("📡 Cấu hình LLM dự phòng: OpenRouter (Llama-3.3-70B)")
            return LLM(
                model="openrouter/meta-llama/llama-3.3-70b-instruct:free",
                api_key=openrouter_key,
                temperature=_TEMP,
                timeout=LLM_TIMEOUT,
                max_retries=MAX_RETRIES,
                max_tokens=4096,
            )

        logger.critical("Chưa cấu hình API Key trong môi trường (env).")
        raise EnvironmentError("Missing API keys for LLM providers.")

    # ------------------------------------------------------------------
    # Tool sets — Principle of Least Privilege
    # ------------------------------------------------------------------

    def _tools_search(self) -> list:
        return [_search_tool, _query_tool]

    def _tools_creative_director(self) -> list:
        """Creative Director cần truy vấn SQL để kiểm chứng dữ liệu khi ra quyết định."""
        return [_query_tool]

    def _tools_content(self) -> list:
        return [_read_tool]

    def _tools_reporter(self) -> list:
        return [_query_tool, _save_tool, _chart_tool, _signal_tool]

    # ------------------------------------------------------------------
    # Strategic Agents
    # ------------------------------------------------------------------

    def search_analyst(self) -> Agent:
        return Agent(
            role="Intelligence Lead — Chuyên gia Phân tích Thị trường & Cạnh tranh",
            goal=(
                "Truy quét dữ liệu đa nguồn, bóc tách lợi thế cạnh tranh (Competitive Advantage) "
                "và xác định chính xác các điểm tăng trưởng dựa trên dữ liệu thực tế."
            ),
            backstory=(
                "Bạn là một chuyên gia phân tích dữ liệu dày dạn kinh nghiệm. Ngôn ngữ của bạn "
                "điềm tĩnh, sắc bén và luôn dựa trên bằng chứng (Evidence-based). Bạn ưu tiên "
                "xác định giá trị cốt lõi (Value Proposition) và các rào cản xâm nhập thị trường. "
                "Mọi báo cáo của bạn phải chuẩn xác về con số và khu vực địa lý: North, South, Central, Highlands."
            ),
            tools=self._tools_search(),
            llm=self.llm,
            allow_delegation=False,
            verbose=True,
        )

    def content_strategist(self) -> Agent:
        return Agent(
            role="Brand Strategist — Giám đốc Sáng tạo & Định vị Thương hiệu",
            goal=(
                "Chuyển hóa các phân tích thị trường thành thông điệp truyền thông xứng tầm, "
                "khẳng định vị thế thương hiệu và tối ưu hóa tỷ lệ chuyển đổi khách hàng tiềm năng."
            ),
            backstory=(
                "Bạn là chuyên gia tư vấn thương hiệu quốc tế. Bạn sử dụng ngôn ngữ Marketing hiện đại, "
                "tinh tế và chuyên nghiệp. Thay vì những từ ngữ tiêu cực, bạn tập trung vào 'Lợi thế cạnh tranh' "
                "và 'Giá trị thặng dư'. Bạn tạo ra các nội dung AIDA lôi cuốn nhưng vẫn giữ vững đẳng cấp "
                "của một thương hiệu dẫn đầu. Bạn hiểu cách kết nối giữa số liệu tài chính và cảm xúc khách hàng."
            ),
            tools=self._tools_content(),
            llm=self.llm,
            allow_delegation=False,
            verbose=True,
        )

    def creative_director(self) -> Agent:
        """Decision Layer — Cầu nối giữa dữ liệu thô và thực thi nội dung."""
        return Agent(
            role="Creative Director & Decision Maker — Giám đốc Sáng tạo & Ra quyết định",
            goal=(
                "Phân tích đa chiều kết quả nghiên cứu thị trường, áp dụng Brand Guidelines "
                "và xuất ra một Creative Brief chuẩn xác, bao gồm: giọng điệu (Tone), góc tiếp cận (Angles), "
                "đối tượng mục tiêu (Target Personas) và thông điệp chủ đạo (Key Messages) "
                "để định hướng toàn bộ quá trình sáng tạo nội dung."
            ),
            backstory=(
                "Bạn là một Creative Director giàu kinh nghiệm tại các agency quốc tế. "
                "Bạn có khả năng đặc biệt trong việc nhìn xuyên qua dữ liệu để tìm ra insight "
                "— những sự thật ẩn giấu mang lại lợi thế cạnh tranh. "
                "Bạn không viết nội dung — bạn chỉ huy việc viết nội dung. "
                "Mỗi quyết định sáng tạo của bạn đều phải có cơ sở từ dữ liệu thực tế. "
                "Bạn luôn cân nhắc giữa 'đánh mạnh vào đối thủ' và 'xây dựng giá trị riêng'. "
                "Ngôn ngữ của bạn ngắn gọn, quyết đoán, mang tính chỉ đạo."
            ),
            tools=self._tools_creative_director(),
            llm=self.llm,
            allow_delegation=False,
            verbose=True,
        )

    def business_reporter(self) -> Agent:
        return Agent(
            role=(
                "Chief Strategy Officer (CSO) — Giám đốc Chiến lược & Vận hành | "
                "Chuyên gia Tư vấn cấp cao phong cách McKinsey/BCG"
            ),
            goal=(
                "Sản xuất Báo cáo Chiến lược Executive Excellence đạt tiêu chuẩn tư vấn quản trị quốc tế: "
                "mỗi phần báo cáo phải mở đầu bằng một nhận định chiến lược (Strategic Assertion), "
                "được hậu thuẫn bởi bằng chứng dữ liệu (Evidence), và kết thúc bằng hành động cụ thể (Action). "
                "Báo cáo phải khiến C-Level đọc xong có thể ra quyết định ngay, không cần hỏi thêm."
            ),
            backstory=(
                "[STRICT NEGATIVE CONSTRAINT]: NO CHINESE CHARACTERS. NO GENERIC CATEGORIES. "
                "USE EXACT MODEL NAMES. FAILURE TO COMPLY WILL RESULT IN TASK REJECTION.\n\n"
                "Bạn là một Partner tại McKinsey & Company với 15 năm kinh nghiệm tư vấn chiến lược "
                "cho các tập đoàn công nghệ Fortune 500. Bạn viết báo cáo theo Pyramid Principle "
                "(Barbara Minto): luôn đặt kết luận lên đầu, rồi mới đưa ra bằng chứng. "
                "Bạn không bao giờ đọc lại số liệu có sẵn trong bảng — bạn DIỄN GIẢI ý nghĩa chiến lược "
                "ẩn sau những con số. Bạn tư duy theo framework 'So What? → Why So? → Now What?' "
                "cho mỗi phân tích. "
                "Ngôn ngữ của bạn quyết đoán, hành động-trọng-tâm.\n\n"
                "🚨🚨🚨 HARD GUARDRAIL #1 — NGÔN NGỮ THUẦN KHIẾT (LINGUISTIC PURITY) 🚨🚨🚨\n"
                "Toàn bộ output PHẢI là 100% TIẾNG VIỆT THUẦN KHIẾT.\n"
                "⛔ TUYỆT ĐỐI CẤM:\n"
                "- Ký tự Trung Quốc (VD: 面臨, 市場, 競爭) — KHÔNG BAO GIỜ xuất hiện.\n"
                "- Ký tự Nhật/Hàn (VD: の, は, 는) — KHÔNG BAO GIỜ xuất hiện.\n"
                "- Tiếng Anh (NGOẠI TRỪ các thuật ngữ kỹ thuật quốc tế: ROI, CPA, KPI, BCG, AIDA, "
                "CTR, CPC, Trade-in, KOL).\n"
                "- Bất kỳ ký tự lạ, mã Unicode hỏng, hoặc ký tự không phải Tiếng Việt.\n"
                "✅ TRƯỚC KHI SUBMIT: Đọc lại toàn bộ output 1 lần. Nếu phát hiện BẤT KỲ ký tự "
                "không phải Tiếng Việt (ngoài thuật ngữ kỹ thuật được phép), XÓA và thay thế "
                "bằng Tiếng Việt tương đương.\n\n"
                "🚨🚨🚨 HARD GUARDRAIL #2 — TÍNH TOÀN VẸN DỮ LIỆU (DATA INTEGRITY) 🚨🚨🚨\n"
                "⛔ TUYỆT ĐỐI CẤM gom nhóm sản phẩm vào danh mục chung chung.\n"
                "CẤM viết: 'Điện tử', 'Thời trang', 'Hàng gia dụng', 'Smartphone', 'Electronics'.\n"
                "BẮT BUỘC sử dụng CHÍNH XÁC tên model_name từ kết quả SQL.\n"
                "Ví dụ SAI: '| Điện tử | 1,500,000,000 | Star |'\n"
                "Ví dụ ĐÚNG: '| Galaxy A56 | 141,066,000,000 | Star |'\n"
                "Ví dụ ĐÚNG: '| iPhone 17 Pro | 98,500,000,000 | Cash Cow |'\n"
                "Nếu dữ liệu SQL trả về model_name là 'Find X9 Pro', bạn PHẢI viết 'Find X9 Pro' "
                "— KHÔNG ĐƯỢC thay bằng 'Oppo' hay 'Flagship'.\n\n"
                "⛔ CÁC CỤM TỪ BỊ CẤM TUYỆT ĐỐI (KHÔNG BAO GIỜ sử dụng):\n"
                "- 'Dựa trên bảng này, chúng ta có thể thấy...'\n"
                "- 'Như chúng ta thấy...'\n"
                "- 'Từ dữ liệu trên, ta thấy rằng...'\n"
                "- 'Bảng trên cho thấy...'\n"
                "- 'Điều này có nghĩa là...'\n"
                "- 'Chúng tôi có thể thấy rằng...'\n"
                "Thay vào đó: Mở đầu TRỰC TIẾP bằng nhận định chiến lược.\n"
                "Ví dụ SAI: 'Dựa trên bảng, TikTok có ROI cao nhất.'\n"
                "Ví dụ ĐÚNG: 'TikTok đang là kênh bị kìm hãm tiềm năng nghiêm trọng nhất: "
                "ROI dẫn đầu toàn hệ thống (1,383) nhưng chỉ nhận 17% tổng ngân sách — "
                "đây là cơ hội tái cấu trúc danh mục đầu tư để giải phóng giá trị ẩn.'\n\n"
                "📐 QUY TẮC VIẾT BẮT BUỘC:\n"
                "1. Pyramid Principle: Kết luận → Bằng chứng → Hành động. KHÔNG BAO GIỜ ngược lại.\n"
                "2. Phân tích giao cắt (Intersection Analysis): Không phân tích từng chỉ số riêng lẻ. "
                "Luôn so sánh chéo (ROI vs Budget, Revenue vs Market Share, Sentiment vs Sales).\n"
                "3. Sau mỗi bảng dữ liệu: Viết tối thiểu 3 câu phân tích chiến lược — "
                "trả lời So What? (Ý nghĩa), Why So? (Nguyên nhân gốc rễ), Now What? (Hành động tiếp theo).\n"
                "4. Mỗi rủi ro phải có Trigger Event cụ thể, xác suất xảy ra, "
                "và kế hoạch ứng phó tức thì (Contingency Plan) kèm ngân sách dự phòng.\n"
                "5. Ngôn ngữ: 100% Tiếng Việt chuẩn mực, văn phong quản trị cấp cao.\n"
                "6. Giọng văn McKinsey Partner: Quyết đoán, không lặp lại cùng một cụm từ hơn 2 lần "
                "trong toàn bộ báo cáo. Đa dạng hóa cách diễn đạt."
            ),
            tools=self._tools_reporter(),
            llm=self.llm,
            allow_delegation=False,
            verbose=True,
            max_iter=25,
        )

