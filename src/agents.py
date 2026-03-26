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
        Truy vấn SQLite marketing_intelligence.db.
        - output_format: "markdown" (để xem/viết báo cáo) hoặc "json" (để vẽ biểu đồ).
        Bảng: sales, competitor_products, social_sentiment, marketing_campaigns, sales_performance.
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
        api_key = os.getenv("NVIDIA_NIM_API_KEY") or os.getenv("NVIDIA_API_KEY")

        if not api_key:
            raise EnvironmentError(
                "NVIDIA_NIM_API_KEY chưa được set.\n"
                "Thêm dòng sau vào file .env rồi chạy lại:\n"
                "  NVIDIA_NIM_API_KEY=your_key_here"
            )

        try:
            print("Khởi tạo LLM: NVIDIA NIM (nvidia_nim/meta/llama-3.3-70b-instruct)...")
            return LLM(
                model="nvidia_nim/meta/llama-3.3-70b-instruct",
                api_key=api_key,
                temperature=0.2,
            )
        except Exception as e:
            raise RuntimeError(f"Khởi tạo LLM thất bại: {e}")

    # ------------------------------------------------------------------
    # Tool sets — mỗi agent chỉ nhận tool cần thiết (least privilege)
    # ------------------------------------------------------------------

    def _tools_search(self) -> list:
        return [_search_tool, _query_tool]

    def _tools_content(self) -> list:
        return [_query_tool, _read_tool]

    def _tools_reporter(self) -> list:
        return [_query_tool, _save_tool, _chart_tool]

    # ------------------------------------------------------------------
    # Agents
    # ------------------------------------------------------------------

    def search_analyst(self) -> Agent:
        return Agent(
            role="Trưởng phòng Kinh doanh & Phân tích Thị trường Bán lẻ",
            goal=(
                "Theo dõi thị trường smartphone và đối chiếu với tồn kho/doanh số "
                "tại đại lý để đưa ra quyết định nhập hàng và định giá tối ưu."
            ),
            backstory=(
                "Bạn là chuyên gia phân tích cho một chuỗi cửa hàng smartphone lớn. "
                "Thay vì sản xuất, bạn tập trung vào: Nhập dòng nào? "
                "Giá bán so với đối thủ (Apple Store, TGDD, CellphoneS) thế nào? "
                "Phân khúc khách hàng nào đang tăng trưởng? "
                "Đưa ra insight để tối ưu hóa doanh số bán lẻ."
            ),
            tools=self._tools_search(),
            llm=self.llm,
            allow_delegation=False,
            verbose=True,
        )

    def content_strategist(self) -> Agent:
        return Agent(
            role="Chuyên gia sáng tạo nội dung MXH",
            goal=(
                "Biến dữ liệu thô từ thị trường và cảm xúc khách hàng thành các mẫu "
                "bài đăng viral trên mạng xã hội để thu hút tương tác và chốt đơn."
            ),
            backstory=(
                "Bạn là một Creative Director với bộ óc nhạy bén về trend. "
                "Nhiệm vụ của bạn không phải là phân tích khô khan, mà là tìm ra góc nhìn "
                "thú vị nhất từ dữ liệu (social_sentiment) để viết caption, tạo hashtag "
                "và đề xuất ý tưởng hình ảnh chuẩn 'viral' cho các kênh Social Media."
            ),
            tools=self._tools_content(),
            llm=self.llm,
            allow_delegation=False,
            verbose=True,
        )

    def business_reporter(self) -> Agent:
        return Agent(
            role="Chiến lược gia tăng trưởng",
            goal=(
                "Tổng hợp Cố vấn Kế hoạch Hành động Tuần bao gồm đối tượng mục tiêu, "
                "kênh ưu tiên và thông điệp chủ đạo, trình bày chuyên nghiệp trên Web."
            ),
            backstory=(
                "Thay vì chỉ thống kê con số, bạn đóng vai trò là não bộ chiến lược. "
                "Từ dữ liệu doanh thu (sales) và chiến dịch (marketing_campaigns), "
                "bạn chỉ ra đích xác phải làm gì tiếp theo: Kênh nào đang hiệu quả? "
                "Cần chạy thông điệp gì ở khung giờ nào? Bạn gợi ý chiến lược tăng trưởng "
                "bằng các Action Items (nhiệm vụ hành động) cụ thể để Team Marketing thực thi ngay."
            ),
            tools=self._tools_reporter(),
            llm=self.llm,
            allow_delegation=False,
            verbose=True,
        )
