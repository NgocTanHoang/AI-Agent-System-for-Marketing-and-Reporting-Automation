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

try:
    from src.tools import (
        EnterpriseDataTools,
        publish_to_google_docs,
        save_report,
        search_internet,
    )

    _db = EnterpriseDataTools()

    @tool("query_marketing_db")
    def query_marketing_db(query: str) -> str:
        """
        Truy vấn SQLite marketing_intelligence.db (sales, competitor_products,
        social_sentiment, marketing_campaigns, sales_performance). Chỉ dùng SELECT.
        """
        return _db.query_marketing_db(query)

    search_tool = search_internet
    save_tool = save_report
    publish_tool = publish_to_google_docs
    query_tool = query_marketing_db
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
        return [t for t in (query_tool, save_tool, publish_tool) if t is not None]

    def search_analyst(self) -> Agent:
        return Agent(
            role="Chuyên gia Phân tích Thị trường Công nghệ",
            goal="Tìm xu hướng smartphone và đối chiếu với dữ liệu trong database.",
            backstory=(
                "Bạn phân tích kép: tìm tin trên Internet và truy vấn DB doanh số/đối thủ "
                "để đưa insight kinh doanh smartphone."
            ),
            tools=self._tools_search(),
            llm=self.llm,
            allow_delegation=False,
            verbose=True,
        )

    def content_strategist(self) -> Agent:
        return Agent(
            role="Chuyên viên Chiến lược Nội dung Công nghệ",
            goal="Xây dựng nội dung marketing dựa trên sentiment trong database.",
            backstory=(
                "Bảng social_sentiment có: keyword, positive_score, negative_score, "
                "top_complaint, trending_platform. Không có cột sentiment hay topic. "
                "Ví dụ: SELECT keyword, positive_score, top_complaint FROM social_sentiment "
                "ORDER BY positive_score DESC. Kết hợp dữ liệu để viết caption và ý tưởng sự kiện."
            ),
            tools=self._tools_content(),
            llm=self.llm,
            allow_delegation=False,
            verbose=True,
        )

    def business_reporter(self) -> Agent:
        return Agent(
            role="Chuyên viên Báo cáo Chiến lược Thị trường",
            goal="Truy vấn DB, viết báo cáo markdown có số liệu thật; xuất bản Google Docs khi công cụ sẵn có.",
            backstory=(
                "Bắt buộc dùng tool query_marketing_db để lấy số liệu; không bịa số. "
                "Schema: sales, sales_performance, competitor_products, social_sentiment, marketing_campaigns. "
                "Sau khi hoàn thành báo cáo, gọi publish_to_google_docs("
                'title="Smartphone Market Strategic Report 2026", content=<toàn bộ markdown>). '
                "Nếu thiếu GOOGLE_DOCS_FOLDER_ID hoặc OAuth, ghi rõ trong kết quả và vẫn lưu nội dung qua save_report nếu có."
            ),
            tools=self._tools_reporter(),
            llm=self.llm,
            allow_delegation=False,
            verbose=True,
        )
