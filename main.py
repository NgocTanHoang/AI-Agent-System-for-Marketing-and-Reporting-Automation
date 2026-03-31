"""
Entry point cho AI Marketing Agent pipeline - Production Version.
"""
import os
import sys
import time
from datetime import datetime

# Windows encoding fix
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

from src.config import setup_logging, validate_config, PROCESSED_DATA_DIR, MAX_RETRIES
from src.agents import MarketingAgents
from src.tasks import MarketingTasks
from crewai import Crew, Process

# Initialize logger for main process
logger = setup_logging("pipeline_main")

def run_smartphone_intelligence_system():
    """
    Khởi chạy pipeline 3 agent tuần tự với cơ chế Error Resilience.
    """
    # 1. Validation bước đầu
    validate_config()
    
    logger.info("Khởi tạo các thành phần hệ thống...")
    try:
        agents_factory = MarketingAgents()
        tasks_factory  = MarketingTasks()
        
        search_analyst     = agents_factory.search_analyst()
        content_strategist = agents_factory.content_strategist()
        business_reporter  = agents_factory.business_reporter()
    except Exception as e:
        logger.critical(f"Lỗi khởi tạo Agent Factory: {e}")
        raise

    # 2. Xây dựng Task Pipeline
    research_task = tasks_factory.research_task(
        agent=search_analyst,
        market_topic="Xu hướng smartphone 2026 và thị trường AI Phone",
    )
    content_task = tasks_factory.content_creation_task(
        agent=content_strategist,
        research_task=research_task,
    )
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

    # 3. Cấu hình Crew
    crew = Crew(
        agents=[search_analyst, content_strategist, business_reporter],
        tasks=[research_task, content_task, data_task, report_task],
        process=Process.sequential,
        memory=False,
        verbose=True,
    )

    logger.info("=" * 40)
    logger.info("🚀 BẮT ĐẦU PIPELINE CHIẾN LƯỢC")
    logger.info("=" * 40)

    result = None
    retry_delay = 30
    
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.info(f"⚡ Thôi thi hành Lần #{attempt}...")
            result = crew.kickoff()
            break 
        except Exception as e:
            err_str = str(e)
            is_retryable = any(k in err_str for k in [
                "Timeout", "504", "502", "503", "ConnectionError", "ReadTimeout", "litellm.Timeout"
            ])
            if is_retryable and attempt < MAX_RETRIES:
                logger.warning(f"Lỗi mạng/Timeout: {err_str[:100]}. Thử lại sau {retry_delay}s...")
                time.sleep(retry_delay)
                retry_delay *= 2
            else:
                logger.error(f"Lỗi nghiêm trọng không thể tự phục hồi: {e}")
                raise

    if not result:
        raise RuntimeError("Pipeline kết thúc mà không có kết quả.")

    # 4. Lưu sản phẩm cuối cùng
    try:
        report_filename = f"Smartphone_Strategic_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        report_path = PROCESSED_DATA_DIR / report_filename
        
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(result.raw)
            
        logger.info("=" * 40)
        logger.info("✅ PIPELINE HOÀN TẤT THÀNH CÔNG")
        logger.info(f"📁 Báo cáo: {report_path.name}")
        logger.info("=" * 40)
    except Exception as e:
        logger.error(f"Lỗi khi lưu báo cáo cuối cùng: {e}")

    return result

if __name__ == "__main__":
    try:
        run_smartphone_intelligence_system()
    except Exception as e:
        logger.error(f"Hệ thống dừng do lỗi: {e}")
        sys.exit(1)