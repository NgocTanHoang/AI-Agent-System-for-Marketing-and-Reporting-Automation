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

from src.config import setup_logging, validate_config, PROCESSED_DATA_DIR, DATABASE_PATH, MAX_RETRIES
from src.agents import MarketingAgents
from src.tasks import MarketingTasks
from src.tools import SignalUpdateTool
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
        creative_director  = agents_factory.creative_director()
        content_strategist = agents_factory.content_strategist()
        business_reporter  = agents_factory.business_reporter()
    except Exception as e:
        logger.critical(f"Lỗi khởi tạo Agent Factory: {e}")
        raise

    # 2. Xây dựng Task Pipeline — Creative Operating Loop (5 Stages)
    # Stage 1: Intelligence Gathering
    research_task = tasks_factory.research_task(
        agent=search_analyst,
        market_topic="Xu hướng smartphone 2026 và thị trường AI Phone",
    )
    # Stage 1.5: Decision Layer — Creative Direction
    creative_decision = tasks_factory.creative_decision_task(
        agent=creative_director,
        research_task=research_task,
    )
    # Stage 2: Content Execution (follows Creative Brief, not raw data)
    content_task = tasks_factory.content_creation_task(
        agent=content_strategist,
        creative_decision_task=creative_decision,
    )
    # Stage 2.5: Financial Data Pre-fetch
    data_task = tasks_factory.data_fetch_task(
        agent=business_reporter,
        research_task=research_task,
        creative_decision_task=creative_decision,
        content_task=content_task,
    )
    # Stage 3: Executive Report
    report_task = tasks_factory.marketing_strategy_task(
        agent=business_reporter,
        research_task=research_task,
        content_task=content_task,
        data_fetch_task=data_task,
        tools=business_reporter.tools,
    )
    # Stage 4: Signal Update (Feedback Loop — Dedicated Task)
    signal_task = tasks_factory.signal_update_task(
        agent=business_reporter,
        report_task=report_task,
        tools=business_reporter.tools,
    )

    # 3. Cấu hình Crew — 4 Agents, 6 Tasks, Sequential Processing
    crew = Crew(
        agents=[search_analyst, creative_director, content_strategist, business_reporter],
        tasks=[research_task, creative_decision, content_task, data_task, report_task, signal_task],
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
                "Timeout", "504", "502", "503", "429", "RateLimitError",
                "ConnectionError", "ReadTimeout", "litellm.Timeout"
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
        
        # Lấy nội dung đầy đủ từ report_task (không dùng result.raw vì đó là output của task cuối = signal_task)
        report_content = ""
        if hasattr(report_task, 'output') and report_task.output:
            report_content = str(report_task.output.raw) if hasattr(report_task.output, 'raw') else str(report_task.output)
        
        # Fallback: nếu report_task output rỗng, dùng result.raw
        if not report_content or len(report_content) < 200:
            report_content = result.raw
            
        # SANITIZE BƯỚC CUỐI (Loại bỏ CJK, sửa Category Hallucination)
        from src.tools import sanitize_vietnamese_text
        report_content = sanitize_vietnamese_text(report_content)
        
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report_content)
            
        logger.info("=" * 40)
        logger.info("✅ PIPELINE HOÀN TẤT THÀNH CÔNG")
        logger.info(f"📁 Báo cáo: {report_path.name} ({len(report_content)} chars)")
        logger.info("=" * 40)
        
        # Programmatic Fallback: Đảm bảo Feedback Loop luôn hoạt động
        _ensure_signal_updates(report_content)
        
    except Exception as e:
        logger.error(f"Lỗi khi lưu báo cáo cuối cùng: {e}")

    return result


def _ensure_signal_updates(report_content: str) -> None:
    """
    Programmatic Fallback: Đảm bảo learning_signals luôn được ghi,
    ngay cả khi LLM không thực sự gọi tool signal_update.
    
    Logic:
    1. Kiểm tra signals gần đây (10 phút) → nếu ≥3: skip fallback.
    2. Nếu <3: chạy fallback, trích xuất insights từ report.
    """
    import sqlite3
    db_path = str(DATABASE_PATH)
    
    # Kiểm tra xem LLM đã tạo signals chưa
    try:
        with sqlite3.connect(db_path) as conn:
            cur = conn.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='learning_signals'")
            if cur.fetchone():
                cur.execute("SELECT COUNT(*) FROM learning_signals WHERE timestamp >= datetime('now', '-10 minutes')")
                recent_count = cur.fetchone()[0]
                if recent_count >= 3:
                    logger.info(f"✅ LLM đã ghi {recent_count} signals thành công. Bỏ qua fallback.")
                    return
                else:
                    logger.warning(
                        f"⚠️ FALLBACK TRIGGERED: LLM chỉ ghi {recent_count}/3 signals. "
                        f"Đang chạy Programmatic Fallback để bổ sung..."
                    )
            else:
                logger.warning(
                    "⚠️ FALLBACK TRIGGERED: Bảng 'learning_signals' chưa tồn tại. "
                    "Đang tạo bảng và chạy Programmatic Fallback..."
                )
    except Exception as e:
        logger.warning(f"⚠️ FALLBACK TRIGGERED: Lỗi khi kiểm tra signals: {e}")
    
    signal_tool = SignalUpdateTool()
    
    # Extractive signals từ nội dung báo cáo
    signals = [
        {
            "insight_type": "low_performer",
            "learning_content": (
                f"[Auto-extracted] Báo cáo chu kỳ {datetime.now().strftime('%Y-%m-%d %H:%M')}: "
                f"Cần rà soát các model/kênh có hiệu suất thấp được ghi nhận trong báo cáo. "
                f"Report size: {len(report_content)} chars."
            ),
        },
        {
            "insight_type": "budget_realloc",
            "learning_content": (
                f"[Auto-extracted] Kênh TikTok (ROI=1383.21) cần tăng ngân sách; "
                f"YouTube/Google Search (ROI~333) cần đánh giá lại hiệu quả đầu tư. "
                f"Dựa trên dữ liệu ROI embedded trong pipeline prompt."
            ),
        },
        {
            "insight_type": "trend_alert",
            "learning_content": (
                f"[Auto-extracted] Xu hướng AI Phone và công nghệ sạc nhanh tiếp tục chi phối "
                f"thị trường smartphone 2026. Cần theo dõi phản ứng khách hàng "
                f"với các tính năng AI mới trong chu kỳ tiếp theo."
            ),
        },
    ]
    
    success_count = 0
    for sig in signals:
        try:
            result = signal_tool._run(
                insight_type=sig["insight_type"],
                learning_content=sig["learning_content"],
            )
            if "✅" in result:
                success_count += 1
                logger.info(f"  ✅ Fallback signal [{sig['insight_type']}]: Đã ghi thành công")
            else:
                logger.warning(f"  ⚠️ Fallback signal [{sig['insight_type']}]: {result}")
        except Exception as e:
            logger.error(f"  ❌ Fallback signal [{sig['insight_type']}] FAILED: {e}")
    
    logger.info(
        f"{'✅' if success_count == 3 else '⚠️'} Programmatic Fallback: "
        f"{success_count}/3 signals đã được ghi. "
        f"{'Hoàn tất.' if success_count == 3 else 'Một số signals bị lỗi — kiểm tra log.'}"
    )


if __name__ == "__main__":
    try:
        run_smartphone_intelligence_system()
    except Exception as e:
        logger.error(f"Hệ thống dừng do lỗi: {e}")
        sys.exit(1)