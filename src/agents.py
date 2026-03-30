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

        ⚠️⚠️ BẮT BUỘC: Dùng đúng tên cột theo từng bảng:
        1. sales: id, brand, model_name, spec_variant, units_sold, unit_price, region, customer_age_group, payment_method, launch_date (KHÔNG có roi, revenue)
        2. competitor_products: id, brand, model_name, key_features, price_segment, current_price, release_year, strengths, weaknesses (KHÔNG có price)
        3. sales_performance: id, model_name, units_sold, revenue, month_period (chứa revenue)
        4. marketing_campaigns: id, campaign_name, channel, budget, reach, conversions, roi, status, start_date, end_date (ĐÂY là bảng chứa roi)
        5. social_sentiment: id, keyword, positive_score, negative_score, total_mentions, top_complaint, trending_platform, top_emotion

        ❤️ Mẹo: để lấy ROI, dùng: SELECT campaign_name, roi FROM marketing_campaigns
        - output_format: "markdown" hoặc "json"
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
        # 1. Ép buộc dùng NVIDIA NIM
        api_key = os.getenv("NVIDIA_NIM_API_KEY") or os.getenv("NVIDIA_API_KEY")
        
        if api_key:
            print("🚀 Khởi tạo LLM ƯU TIÊN: NVIDIA NIM (meta/llama-3.3-70b-instruct)...")
            return LLM(
                model="nvidia_nim/meta/llama-3.3-70b-instruct", 
                api_key=api_key, 
                temperature=0.2
            )
        
        # 2. Nếu không có NVIDIA, báo lỗi luôn thay vì dùng model tính phí của OpenRouter
        # Hoặc chỉ dùng model FREE thực sự
        openrouter_key = os.getenv("OPENROUTER_API_KEY")
        if openrouter_key:
            print("📡 CẢNH BÁO: Dùng OpenRouter FREE (Chỉ dùng model miễn phí)...")
            return LLM(
                # Phải đảm bảo model ID có chữ :free ở cuối
                model="openrouter/google/gemini-2.0-flash-exp:free", # Ví dụ model free khác
                api_key=openrouter_key,
                temperature=0.2,
            )
            
        raise EnvironmentError("Bệ hạ chưa nạp API Key vào file .env rồi!")

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
            role="Trưởng phòng Tình báo Thị trường & Đối thủ (Market Intelligence Lead)",
            goal=(
                "Thực hiện 'truy quét' dữ liệu từ Internet và SQL để bóc tách chiến thuật của đối thủ (Apple, Samsung, Xiaomi) "
                "và tìm ra các điểm yếu (Gaps) trong chuỗi cung ứng/giá bán để tấn công thị trường."
            ),
            backstory=(
                "BẠN LÀ MỘT 'BỘ ÓC TÌNH BÁO' SẮC SẢO. Thay vì liệt kê số liệu chung chung, bạn phải: "
                "1. Data Integrity: Trích xuất số liệu thực (Price, Stock) từ SQL. Lưu ý dùng 'model_name' và 'unit_price' (KHÔNG dùng 'model' hay 'price'). "
                "2. Competitive Benchmarking: So sánh trực tiếp key_features (Chip, Pin, Camera) của ta với đối thủ từ bảng 'competitor_products'. "
                "3. Insight Thực chiến: Chỉ ra tại sao khách hàng lại chọn đối thủ thay vì ta (Ví dụ: 'Apple đang thắng ở phân khúc Gen Z nhờ Trade-in hời hơn')."
            ),
            tools=self._tools_search(),
            llm=self.llm,
            allow_delegation=False,
            verbose=True,
        )

    def content_strategist(self) -> Agent:
        return Agent(
            role="Giám đốc Sáng tạo Gen Z & Viral Growth Hacker (CSO - Chief Slay Officer)",
            goal=(
                "Biến các nỗi đau của khách hàng (pain points) và thông số kỹ thuật khô khan thành "
                "các nội dung 'Toxic nhẹ', 'Flexing' hoặc 'Slay' để thu hút Gen Z và đẩy phễu bán hàng."
            ),
            backstory=(
                "BẠN LÀ MỘT 'CHÚA TỂ CONTENT'. Văn phong của bạn phải cực kỳ 'thời thượng': "
                "1. Từ khóa bắt buộc: Slay, Flex, Chill, Check-var, 32 củ, 'phát cơm chó', 'hết nước chấm'. "
                "2. Tư duy so sánh: 'iPhone 17 Pro giá 32 củ nhưng sạc vẫn chậm hơn rùa? Qua đây xem S26 Ultra sạc 30 phút đầy bình!'. "
                "3. Tuyệt đối trung thực: Luôn dùng REAL DATA từ Research agent. Khi truy vấn SQL, BẮT BUỘC dùng 'model_name' (KHÔNG dùng 'model'). "
                "Cấu trúc bài đăng: [TIÊU ĐỀ THU HÚT] - [NỘI DUNG CHÍNH (AIDA)] - [CALL TO ACTION] - [10 HASHTAGS TRENDING]."
            ),
            tools=self._tools_content(),
            llm=self.llm,
            allow_delegation=False,
            verbose=True,
        )

    def business_reporter(self) -> Agent:
        return Agent(
            role="Tổng giám đốc Chiến lược & Tăng trưởng (Chief Strategy & Creative Officer)",
            goal=(
                "Hợp nhất dữ liệu Tam giác (SQL + Internet + Content) thành một 'Mật lệnh hành động' "
                "có tính thực chiến cực cao, chỉ ra đích danh model, khu vực và ngân sách cần dồn lực."
            ),
            backstory=(
                "BẠN KHÔNG PHẢI LÀ NGƯỜI LÀM BÁO CÁO, BẠN LÀ 'TỔNG TƯ LỆNH' CHIẾN DỊCH. "
                "1. DATA INTEGRITY: Phải lấy ROI, Doanh thu lẻ đến từng đơn vị từ SQL. Lưu ý dùng 'model_name' (KHÔNG dùng 'model'). "
                "2. Phân tích Đối đầu: Lấy key_features và strengths từ bảng 'competitor_products' để giải mã tại sao thắng/thua. "
                "3. KẾT QUẢ ĐẦU RA: Bắt buộc trả về bản báo cáo bằng Markdown CHUẨN, sử dụng xuống dòng (\n) rõ ràng giữa các mục. "
                "4. Final Answer: Trả về bản báo cáo Markdown thật chi tiết, phân tích sâu (ít nhất 1000 từ). KHÔNG được trả lời vài dòng ngắn ngủi. BẠN PHẢI TỔNG HỢP CẢ NỘI DUNG TỪ CONTENT SPECIALIST VÀO ĐÂY."
            ),
            tools=self._tools_reporter(),
            llm=self.llm,
            allow_delegation=False,
            verbose=True,
        )
