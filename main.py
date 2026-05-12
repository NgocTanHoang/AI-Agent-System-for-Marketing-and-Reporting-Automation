"""
Entry point cho AI Marketing Agent pipeline - Production Version.
"""
import os
import sys
import time
import uuid
from datetime import datetime

# Windows encoding fix
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

from src.config import (
    DATABASE_PATH,
    MAX_RETRIES,
    PROCESSED_DATA_DIR,
    load_pipeline_settings,
    setup_logging,
    validate_config,
)
from src.agents import MarketingAgents
from src.tasks import MarketingTasks
from src.tools import SignalUpdateTool
from src.memory import (
    build_memory_context,
    count_signals_for_run,
    write_signal,
    log_run,
)
from src.runtime_data import (
    build_channel_roi_reference,
    build_signal_fallback_entries,
    format_regions,
)
from src.reporting import missing_required_sections
from crewai import Crew, Process

# Initialize logger for main process
logger = setup_logging("pipeline_main")

def run_smartphone_intelligence_system():
    """
    Khởi chạy pipeline 3 agent tuần tự với cơ chế Error Resilience.
    """
    # 1. Validation bước đầu
    validate_config()
    settings = load_pipeline_settings()
    run_id = str(uuid.uuid4())[:8]
    start_time = time.time()
    qa_passed = False  # Track QA result for audit trail

    # --- MEMORY LAYER: Đọc bài học từ các chu kỳ trước ---
    memory_context = build_memory_context(
        limit=settings["pipeline"]["feedback_signal_limit"],
        lookback_days=settings["pipeline"]["feedback_lookback_days"],
    )
    logger.info("🧠 Memory Context loaded: %d chars", len(memory_context))

    # --- BRAND KNOWLEDGE: Auto-index Brand Guidelines vào Vector DB ---
    try:
        from src.vector_db import BrandKnowledgeDB
        kb = BrandKnowledgeDB()
        if kb.count() == 0:
            logger.info("📚 Auto-indexing Brand Guidelines vào Vector DB...")
            index_result = kb.index_brand_files()
            logger.info("✅ Brand Knowledge indexed: %s", index_result)
        else:
            logger.info("✅ Brand Knowledge DB sẵn sàng (%d chunks)", kb.count())
    except Exception as e:
        logger.warning(f"Lỗi khi index Brand Knowledge: {e}. Agent sẽ dùng fallback (read_marketing_content).")

    # Dynamic Few-Shot Prompting (RAG)
    vector_db = None
    few_shot_context = ""
    try:
        from src.vector_db import ReportHistoryDB
        vector_db = ReportHistoryDB()
        similar_reports = vector_db.get_similar_reports(settings['pipeline']['market_topic'], n_results=3)
        if similar_reports:
            few_shot_context = "\n\nCAC BAO CAO TUYET VOI TU TRUOC DE THAM KHAO THEO YEU CAU:\n" + "\n---\n".join(similar_reports)
    except Exception as e:
        logger.warning(f"Lỗi khi load Vector DB: {e}")

    # Override prompt anchors at runtime so the legacy task definitions stay intact.
    import src.tasks as task_module

    task_module._REGIONS = format_regions(settings)
    task_module._ROI_DATA = build_channel_roi_reference(settings=settings)
    task_module._REGION_NOTE = f"CHI DUNG CAC KHU VUC NAY: {task_module._REGIONS}"

    logger.info("Khởi tạo các thành phần hệ thống...")
    try:
        agents_factory = MarketingAgents()
        tasks_factory  = MarketingTasks()
        
        search_analyst     = agents_factory.search_analyst()
        creative_director  = agents_factory.creative_director()
        content_strategist = agents_factory.content_strategist()
        business_reporter  = agents_factory.business_reporter()
        qa_reviewer        = agents_factory.quality_assurance_agent()
    except Exception as e:
        logger.critical(f"Lỗi khởi tạo Agent Factory: {e}")
        raise

    # 2. Xây dựng Task Pipeline — Creative Operating Loop (5 Stages)
    # Stage 1: Intelligence Gathering
    research_task = tasks_factory.research_task(
        agent=search_analyst,
        market_topic=(
            f"{settings['pipeline']['market_topic']}\n\n"
            f"{memory_context}\n\n"
            f"{few_shot_context}"
        ),
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
    # Stage 2.5: Financial Data Pre-fetch (Search Analyst does pure data retrieval)
    data_task = tasks_factory.data_fetch_task(
        agent=search_analyst,
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
    # Backup: CrewAI auto-saves report output in case manual save fails
    report_output_filename = f"{settings['pipeline']['report_prefix']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    report_task.output_file = str(PROCESSED_DATA_DIR / report_output_filename)
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
    
    # Error Resilience: External LLM Call Backoff
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.info(f"⚡ Thực thi Pipeline Lần #{attempt}...")
            result = crew.kickoff()
            break 
        except Exception as e:
            err_str = str(e)
            is_retryable = any(k in err_str for k in [
                "Timeout", "504", "502", "503", "429", "RateLimitError",
                "ConnectionError", "ReadTimeout", "litellm.Timeout"
            ])
            if is_retryable and attempt < MAX_RETRIES:
                logger.warning(f"Lỗi API/Mạng: {err_str[:100]}. Đang thử lại sau {retry_delay}s...")
                time.sleep(retry_delay)
                retry_delay *= 2
            else:
                logger.error(f"Lỗi nghiêm trọng không thể tự phục hồi (Hệ thống dừng): {e}")
                raise e

    if not result:
        raise RuntimeError("Pipeline kết thúc mà không có kết quả (Null Result).")

    # --- PRINCIPAL ENGINEER'S REFLECTION LOOP (LLM-AS-A-JUDGE) ---
    # Ngăn chặn Infinite Loop và đảo bảo tính chính xác của báo cáo.
    
    report_content = ""
    try:
        # Extract report from task output — multi-version CrewAI compatibility
        if hasattr(report_task, 'output') and report_task.output is not None:
            task_output = report_task.output
            if hasattr(task_output, 'raw'):
                report_content = str(task_output.raw)
            elif hasattr(task_output, 'result'):
                report_content = str(task_output.result)
            elif hasattr(task_output, '__str__'):
                report_content = str(task_output)

        if not report_content or len(report_content) < 300:
            logger.warning("Nội dung báo cáo mục tiêu quá ngắn, sử dụng toàn bộ pipeline result làm fallback.")
            if hasattr(result, 'raw'):
                report_content = str(result.raw)
            elif hasattr(result, 'result'):
                report_content = str(result.result)
            else:
                report_content = str(result)

        data_fetch_output = ""
        if hasattr(data_task, 'output') and data_task.output is not None:
            if hasattr(data_task.output, 'raw'):
                data_fetch_output = str(data_task.output.raw)
            else:
                data_fetch_output = str(data_task.output)

        MAX_REFLECTION_LOOPS = 2
        for loop_idx in range(MAX_REFLECTION_LOOPS):
            logger.info(f"🔍 [Judge] Kiểm duyệt chất lượng báo cáo (Vòng lặp {loop_idx+1}/{MAX_REFLECTION_LOOPS})...")

            qa_task_instance = tasks_factory.qa_task(qa_reviewer, report_content, data_fetch_output)
            qa_crew = Crew(agents=[qa_reviewer], tasks=[qa_task_instance], process=Process.sequential, verbose=True)
            qa_result = qa_crew.kickoff()

            qa_critique = qa_result.raw if hasattr(qa_result, 'raw') else str(qa_result)

            if "PASSED" in qa_critique.upper():
                logger.info("✅ Báo cáo đạt chuẩn Tuyệt đối (PASSED). Kết thúc Reflection Loop.")
                qa_passed = True
                break

            if loop_idx < MAX_REFLECTION_LOOPS - 1:
                logger.warning(f"⚠️ QA phát hiện lỗi nghiêm trọng: {qa_critique[:200]}...")
                logger.info("🛠️ Đang yêu cầu Business Reporter tái cấu trúc báo cáo dựa trên Critique.")

                refine_task_instance = tasks_factory.refine_report_task(business_reporter, report_content, qa_critique)
                refine_crew = Crew(agents=[business_reporter], tasks=[refine_task_instance], process=Process.sequential, verbose=True)
                refine_result = refine_crew.kickoff()

                if hasattr(refine_result, 'raw'):
                    report_content = str(refine_result.raw)
                else:
                    report_content = str(refine_result)
            else:
                logger.error("🛑 Đạt giới hạn Reflection Loop mà báo cáo vẫn chưa đạt chuẩn PASSED. Tiếp tục lưu bản hiện tại.")

    except Exception as e:
        logger.error(f"Lỗi trong quá trình Reflection Loop (Guardrails failed): {e}")
        # Even if reflection fails, we try to preserve the existing report_content
        if not report_content:
            if hasattr(result, 'raw'):
                report_content = str(result.raw)
            else:
                report_content = str(result)


    # 4. Lưu sản phẩm cuối cùng
    try:
        report_path = PROCESSED_DATA_DIR / report_output_filename
        missing_sections = missing_required_sections(report_content)
        if missing_sections:
            logger.warning(
                "⚠️ Report thiếu các section chiến lược: %s",
                ", ".join(missing_sections),
            )
        else:
            logger.info("✅ Report đạt đủ khung section chiến lược tối thiểu.")
        
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report_content)
            
        logger.info("=" * 40)
        logger.info("✅ PIPELINE HOÀN TẤT THÀNH CÔNG")
        logger.info(f"📁 Báo cáo: {report_path.name} ({len(report_content)} chars)")
        logger.info("=" * 40)
        
        # Lưu báo cáo vào Vector DB (Lịch sử báo cáo tốt) sẽ được thực hiện qua UI (Thumbs Up)
        # Vector DB insertion removed here.

        # Programmatic Fallback: Đảm bảo Feedback Loop luôn hoạt động
        _ensure_signal_updates(report_content, run_id=run_id, settings=settings)

        # Ghi run history vào memory.db (audit trail)
        try:
            elapsed = time.time() - start_time
            log_run(
                run_id=run_id,
                market_topic=settings['pipeline']['market_topic'],
                report_filename=report_output_filename,
                report_length=len(report_content),
                qa_passed=qa_passed,
                duration_seconds=elapsed,
            )
            logger.info(f"💾 Run history ghi nhận: run_id={run_id}, duration={elapsed:.1f}s")
        except Exception as e:
            logger.warning(f"⚠️ Không ghi được run history: {e}")
        
    except Exception as e:
        logger.error(f"Lỗi khi lưu báo cáo cuối cùng: {e}")

    return result


def _ensure_signal_updates(report_content: str, run_id: str = "", settings: dict | None = None) -> None:
    """
    Programmatic Fallback: Đảm bảo learning_signals luôn được ghi vào memory.db,
    ngay cả khi LLM không thực sự gọi tool signal_update.
    
    Logic:
    1. Kiểm tra signals gần đây (10 phút) trong memory.db → nếu ≥3: skip.
    2. Nếu <3: chạy fallback, trích xuất insights từ report.
    """
    settings = settings or load_pipeline_settings()
    recent_window = settings["pipeline"]["signal_recent_window_minutes"]
    
    recent_count = count_signals_for_run(run_id=run_id, minutes=recent_window)
    if recent_count >= 3:
        logger.info(
            "✅ Run %s đã ghi %d signals vào memory.db. Bỏ qua fallback.",
            run_id,
            recent_count,
        )
        return
    
    logger.warning(
        f"⚠️ FALLBACK TRIGGERED: Run {run_id or 'unknown'} chỉ có {recent_count}/3 signals. "
        f"Đang chạy Programmatic Fallback..."
    )
    
    # Trích xuất signals từ nội dung báo cáo
    db_path = str(DATABASE_PATH)
    signals = build_signal_fallback_entries(report_content, db_path=db_path)

    success_count = 0
    for sig in signals:
        try:
            result = write_signal(
                insight_type=sig["insight_type"],
                learning_content=sig["learning_content"],
                run_id=run_id,
            )
            if "✅" in result:
                success_count += 1
                logger.info(f"  ✅ Fallback signal [{sig['insight_type']}]: Đã ghi vào memory.db")
            else:
                logger.warning(f"  ⚠️ Fallback signal [{sig['insight_type']}]: {result}")
        except Exception as e:
            logger.error(f"  ❌ Fallback signal [{sig['insight_type']}] FAILED: {e}")
    
    logger.info(
        f"{'✅' if success_count == 3 else '⚠️'} Programmatic Fallback: "
        f"{success_count}/3 signals đã được ghi vào memory.db. "
        f"{'Đầy đủ.' if success_count == 3 else 'Một số signals bị lỗi.'}"
    )


if __name__ == "__main__":
    try:
        run_smartphone_intelligence_system()
    except Exception as e:
        logger.error(f"Hệ thống dừng do lỗi: {e}")
        sys.exit(1)
