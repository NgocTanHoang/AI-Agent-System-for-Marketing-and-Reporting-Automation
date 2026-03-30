"""
Entry point cho AI Marketing Agent pipeline.
Quy trình: Nghiên cứu -> Phân tích Sentiment -> Báo cáo Chiến lược & Xuất bản.
"""
import os
import sys
from datetime import datetime
from crewai import Crew, Process
from src.agents import MarketingAgents
from src.tasks import MarketingTasks
from src.tools import create_sales_chart


def run_smartphone_intelligence_system():
    """
    Khởi chạy pipeline 3 agent tuần tự:
    1. Search Analyst     — nghiên cứu thị trường
    2. Content Strategist — thiết kế marketing
    3. Business Reporter  — tổng hợp báo cáo cục bộ
    """

    # 1. Khởi tạo factory
    agents_factory = MarketingAgents()   # load_dotenv() được gọi bên trong __init__
    tasks_factory  = MarketingTasks()

    # 2. Khởi tạo agents
    search_analyst     = agents_factory.search_analyst()
    content_strategist = agents_factory.content_strategist()
    business_reporter  = agents_factory.business_reporter()

    # 3. Khởi tạo tasks với context chaining 4 stages
    research_task = tasks_factory.research_task(
        agent=search_analyst,
        market_topic="Xu hướng smartphone 2026 và thị trường AI Phone",
    )
    content_task = tasks_factory.content_creation_task(
        agent=content_strategist,
        research_task=research_task,
    )
    # Stage 2.5: Pre-fetch SQL data để giảm tải token cho Stage 3
    data_task = tasks_factory.data_fetch_task(
        agent=business_reporter,
        research_task=research_task,
        content_task=content_task,
    )
    report_task = tasks_factory.marketing_strategy_task(
        agent=business_reporter,
        research_task=research_task,
        content_task=content_task,
        data_fetch_task=data_task,
        tools=business_reporter.tools,
    )

    # 4. Thiết lập Crew
    crew = Crew(
        agents=[search_analyst, content_strategist, business_reporter],
        tasks=[research_task, content_task, data_task, report_task],
        process=Process.sequential,
        memory=False,   # tắt để tránh phụ thuộc Embedder ngoài
        verbose=True,
    )

    # 5. Chạy pipeline — tự động retry khi gặp Timeout / 5xx (NVIDIA NIM 504)
    import time

    print("\n" + "=" * 60)
    print("🚀 SMARTPHONE INTELLIGENCE SYSTEM — BẮT ĐẦU")
    print(f"   Thời gian : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   Mục tiêu  : Biến dữ liệu thô thành Báo cáo Chiến lược")
    print("=" * 60 + "\n")

    _MAX_RETRIES = 3
    _retry_delay = 30   # giây — bắt đầu 30s, tăng gấp đôi mỗi lần (exponential backoff)

    result = None
    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            print(f"\n⚡ Lần chạy #{attempt}/{_MAX_RETRIES}...")
            result = crew.kickoff()
            print(f"\n[DEBUG]: Độ dài báo cáo: {len(result.raw)} ký tự")
            break   # Thành công → thoát vòng lặp retry

        except Exception as e:
            err_str = str(e)
            is_retryable = any(k in err_str for k in [
                "Timeout", "504", "502", "503", "ConnectionError", "ReadTimeout",
                "NvidiaException", "litellm.Timeout"
            ])
            if is_retryable and attempt < _MAX_RETRIES:
                print(f"\n⚠️  Lần #{attempt} gặp lỗi timeout/5xx: {err_str[:120]}")
                print(f"   Thử lại sau {_retry_delay}s...")
                time.sleep(_retry_delay)
                _retry_delay *= 2   # 30s → 60s → 120s
            else:
                raise   # Lỗi logic hoặc hết retry → cho nổi lên

    if result is None:
        raise RuntimeError("Pipeline thất bại sau tất cả các lần retry.")


    # --- Lưu báo cáo cục bộ ---
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "processed")
    os.makedirs(output_dir, exist_ok=True)
    report_path = os.path.join(output_dir, f"Smartphone_Strategic_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(result.raw)

    print("\n" + "=" * 60)
    print("✅ PIPELINE HOÀN TẤT")
    print(f"   Thời gian : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("   Báo cáo đã được lưu rại data/processed/ và sẵn sàng hiển thị trên Web UI.")
    print("=" * 60 + "\n")

    return result


if __name__ == "__main__":
    try:
        run_smartphone_intelligence_system()
    except EnvironmentError as e:
        # Thiếu API key hoặc credentials
        print(f"\n❌ Lỗi cấu hình môi trường:\n   {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Pipeline thất bại:\n   {e}")
        sys.exit(1)