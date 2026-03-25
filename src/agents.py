"""
Định nghĩa agent CrewAI cho pipeline phân tích thị trường smartphone.
Tools được nạp một lần, xử lý lỗi thống nhất (không còn nhánh fallback thiếu publish_tool).
"""
import os
from dotenv import load_dotenv
from crewai import Agent, LLM
from crewai.llm import BaseLLM
from crewai.tools import tool

# Project root và biến môi trường
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
load_dotenv(os.path.join(project_root, ".env"))

_api_key = os.getenv("NVIDIA_NIM_API_KEY") or os.getenv("NVIDIA_API_KEY")
if _api_key:
    os.environ["NVIDIA_NIM_API_KEY"] = _api_key

# --- Tools: một khối try/except, gán đủ bốn tool hoặc báo lỗi rõ ràng ---
search_tool = None
query_tool = None
save_tool = None
publish_tool = None
chart_tool = None

try:
    from src.tools import (
        EnterpriseDataTools,
        publish_to_google_docs,
        save_report,
        search_internet,
        create_sales_chart,
    )

    _db = EnterpriseDataTools()

    @tool("query_marketing_db")
    def query_marketing_db(query: str, output_format: str = "markdown") -> str:
        """
        Truy vấn SQLite marketing_intelligence.db.
        - output_format: "markdown" (để xem/viết báo cáo) hoặc "json" (để truyền vào tool vẽ biểu đồ).
        Bảng: sales, competitor_products, social_sentiment, marketing_campaigns, sales_performance.
        """
        return _db.query_marketing_db(query, output_format=output_format)

    search_tool = search_internet
    save_tool = save_report
    publish_tool = publish_to_google_docs
    query_tool = query_marketing_db
    chart_tool = create_sales_chart
except Exception as e:
    print(f"Warning: failed to load tools: {e}")


class NoOpLLM(BaseLLM):
    """Dự phòng khi không có NVIDIA API key; CrewAI vẫn gọi được nhưng không sinh nội dung thông minh."""

    def __init__(self):
        super().__init__(model="no-op", temperature=0.0, provider="none")

    def call(
        self,
        messages,
        tools=None,
        callbacks=None,
        available_functions=None,
        from_task=None,
        from_agent=None,
        response_model=None,
    ):
        return (
            "[NoOpLLM] Set NVIDIA_NIM_API_KEY in .env to enable the real LLM."
        )

    async def acall(
        self,
        messages,
        tools=None,
        callbacks=None,
        available_functions=None,
        from_task=None,
        from_agent=None,
        response_model=None,
    ):
        return self.call(
            messages,
            tools=tools,
            callbacks=callbacks,
            available_functions=available_functions,
            from_task=from_task,
            from_agent=from_agent,
            response_model=response_model,
        )


class MarketingAgents:
    """Factory cho ba agent: nghiên cứu, nội dung, báo cáo."""

    def __init__(self):
        self.llm = self._get_llm()

    def _get_llm(self):
        # CrewAI wraps LangChain ChatNVIDIA into LLM(model="meta/...") which is not a
        # native provider; LiteLLM is required. Use nvidia_nim/ prefix so LiteLLM routes
        # to NVIDIA NIM (see https://docs.litellm.ai/docs/providers/nvidia_nim).
        nvidia_api_key = os.getenv("NVIDIA_NIM_API_KEY") or os.getenv("NVIDIA_API_KEY")
        if nvidia_api_key:
            try:
                print(
                    "Starting LLM: NVIDIA NIM via LiteLLM "
                    "(nvidia_nim/meta/llama-3.3-70b-instruct)..."
                )
                return LLM(
                    model="nvidia_nim/meta/llama-3.3-70b-instruct",
                    api_key=nvidia_api_key,
                    temperature=0.2,
                )
            except Exception as e:
                print(f"LLM init failed: {e}")
        print("Warning: no valid NVIDIA_NIM_API_KEY; using NoOpLLM.")
        return NoOpLLM()

    def _tools_search(self):
        return [t for t in (search_tool, query_tool) if t is not None]

    def _tools_content(self):
        return [query_tool] if query_tool else []

    def _tools_reporter(self):
        return [t for t in (query_tool, save_tool, publish_tool, chart_tool) if t is not None]

    def search_analyst(self) -> Agent:
        return Agent(
            role="Trưởng phòng Kinh doanh & Phân tích Thị trường Bán lẻ",
            goal="Theo dõi thị trường smartphone và đối chiếu với tồn kho/doanh số tại đại lý.",
            backstory=(
                "Bạn là chuyên gia phân tích cho một chuỗi cửa hàng smartphone lớn. "
                "Thay vì sản xuất, bạn tập trung vào việc quyết định: Nhập dòng nào? "
                "Giá bán so với đối thủ (Apple Store, TGDD, CellphoneS) thế nào? "
                "Phân khúc khách hàng nào đang tăng trưởng? Đưa ra insight để tối ưu hóa doanh số bán lẻ."
            ),
            tools=self._tools_search(),
            llm=self.llm,
            allow_delegation=False,
            verbose=True,
        )

    def content_strategist(self) -> Agent:
        return Agent(
            role="Quản lý Chiến dịch Marketing & Sự kiện tại Cửa hàng",
            goal="Lên kế hoạch khuyến mãi và sự kiện thu hút khách hàng đến cửa hàng.",
            backstory=(
                "Bạn không phát triển tính năng sản phẩm, bạn phát triển trải nghiệm mua sắm. "
                "Dựa trên dữ liệu cảm xúc (cột top_emotion trong bảng social_sentiment) và phân khúc khách hàng, bạn thiết kế: "
                "Các mẫu ưu đãi, trả góp, sự kiện store để tăng tỷ lệ chốt đơn."
            ),
            tools=self._tools_content(),
            llm=self.llm,
            allow_delegation=False,
            verbose=True,
        )

    def business_reporter(self) -> Agent:
        return Agent(
            role="Giám đốc Vận hành (COO) Chuỗi Bán lẻ",
            goal="Tổng hợp báo cáo hiệu quả kinh doanh, ROI chiến dịch và đề xuất chiến lược nhập hàng/bán hàng.",
            backstory=(
                "Bạn chịu trách nhiệm về lợi nhuận của toàn chuỗi. Bạn cần báo cáo Executive cho Hội đồng quản trị: "
                "Chiến dịch nào mang lại lợi nhuận cao nhất? Nên đẩy mạnh mẫu nào cho Gen Z? "
                "Đối thủ đang giảm giá dòng nào để mình phản ứng kịp thời? "
                "Báo cáo tập trung vào: Doanh số, Lợi nhuận (ROI), Chiến lược giá và Khuyến mãi. "
                "Cuối cùng, xuất bản báo cáo lên Google Docs để Ban quản trị xem xét."
            ),
            tools=self._tools_reporter(),
            llm=self.llm,
            allow_delegation=False,
            verbose=True,
        )
