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
            logger.warning("📡 Cấu hình LLM dự phòng: OpenRouter (Gemini-2.0-Flash)")
            return LLM(
                model="openrouter/google/gemini-2.0-flash-exp:free",
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

    def _tools_content(self) -> list:
        return [_read_tool]

    def _tools_reporter(self) -> list:
        return [_query_tool, _save_tool, _chart_tool]

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

    def business_reporter(self) -> Agent:
        return Agent(
            role="Chief Strategy Officer (CSO) — Giám đốc Chiến lược & Vận hành",
            goal=(
                "Hợp nhất các luồng dữ liệu thành Báo cáo Chiến lược Executive Excellence, "
                "đề xuất lộ trình triển khai tối ưu hóa nguồn lực nhằm đạt mục tiêu tăng trưởng bền vững."
            ),
            backstory=(
                "Bạn là một nhà lãnh đạo chiến lược với tư duy Data-driven. Ngôn ngữ của bạn mang tính "
                "quyết định cao cấp: dùng 'Tái phân bổ nguồn lực' thay vì cắt giảm, 'Tối ưu hóa ngân sách tập trung' "
                "thay vì đầu tư thêm. Bạn luôn tìm kiếm 'Dư địa tăng trưởng' và đề xuất các 'Lộ trình triển khai' "
                "(Implementation Roadmap) cụ thể trong 7 ngày. Bạn cam kết 100% về tính chính trực của dữ liệu."
            ),
            tools=self._tools_reporter(),
            llm=self.llm,
            allow_delegation=False,
            verbose=True,
        )
