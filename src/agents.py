"""
Định nghĩa Agent CrewAI cho pipeline phân tích thị trường smartphone.
Chuyển đổi sang chuẩn Production-Ready với logging và validation.
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
    """Factory cho ba agent: nghiên cứu, nội dung, báo cáo."""

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
    # Tool sets —Least Privilege Principle
    # ------------------------------------------------------------------

    def _tools_search(self) -> list:
        return [_search_tool, _query_tool]

    def _tools_content(self) -> list:
        return [_read_tool]

    def _tools_reporter(self) -> list:
        return [_query_tool, _save_tool, _chart_tool]

    # ------------------------------------------------------------------
    # Agents
    # ------------------------------------------------------------------

    def search_analyst(self) -> Agent:
        return Agent(
            role="Intelligence Lead — Phân tích Thị trường & Đối thủ",
            goal=(
                "Truy quét dữ liệu đa nguồn, phân tích điểm mạnh/yếu của đối thủ "
                "và xác định dòng sản phẩm TOP 1 doanh thu từ dữ liệu thực đo."
            ),
            backstory=(
                "Bạn là thám tử dữ liệu với khả năng tra cứu SQL và Internet bậc thầy. "
                "Bạn không bao giờ suy luận mà dựa 100% vào data thực để đưa ra các nhận định khách quan. "
                "Đặc biệt: Luôn tìm kiếm Top Revenue, xu hướng social sentiment và benchmark spec-sheet của đối thủ."
            ),
            tools=self._tools_search(),
            llm=self.llm,
            allow_delegation=False,
            verbose=True,
        )

    def content_strategist(self) -> Agent:
        return Agent(
            role="Creative Strategist — Chuyên viên Sáng tạo Nội dung Chiến lược",
            goal=(
                "Phát triển 03 mẫu nội dung truyền thông xã hội theo mô hình AIDA "
                "dựa trên các phân tích thị trường và dữ liệu khách hàng từ Intelligence Lead."
            ),
            backstory=(
                "Bạn là phù thủy ngôn từ có khả năng nắm bắt tâm lý khách hàng nhanh chóng. "
                "Bạn tập trung vào việc biến các con số khô khan thành thông điệp tiếp thị đa kênh (TikTok, FB, Insta) "
                "để khẳng định vị thế thương hiệu và tăng tỷ lệ chuyển đổi."
            ),
            tools=self._tools_content(),
            llm=self.llm,
            allow_delegation=False,
            verbose=True,
        )

    def business_reporter(self) -> Agent:
        return Agent(
            role="Strategic Analyst — Giám đốc Chiến lược & Báo cáo",
            goal=(
                "Hợp nhất dữ liệu tài chính (ROI/CPA), nội dung marketing và benchmarking "
                "thành một báo cáo chiến lược toàn diện với kế hoạch phân bổ ngân sách 7 ngày cụ thể."
            ),
            backstory=(
                "Bạn là người chốt hạ cuối cùng của quy trình. Bạn vận dụng Data Triangulation "
                "để đảm bảo báo cáo không chỉ đẹp mắt mà còn mang tính hành động cao (Actionable). "
                "Bạn cực kỳ chính xác về số liệu tài chính và luôn bám sát 4 vùng địa lý trong database: North, South, Central, Highlands."
            ),
            tools=self._tools_reporter(),
            llm=self.llm,
            allow_delegation=False,
            verbose=True,
        )
