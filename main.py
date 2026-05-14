from __future__ import annotations

import sys

from src.config import load_pipeline_settings, setup_logging
from src.memory import count_signals_for_run, write_signal
from src.obsidian.pipeline import ObsidianPipelineService
from src.obsidian.repository import DatabaseTool
from src.runtime_data import build_signal_fallback_entries


logger = setup_logging("obsidian_main")


def _ensure_signal_updates(report_content: str, run_id: str = "", settings: dict | None = None) -> int:
    settings = settings or load_pipeline_settings()
    recent_window = settings["pipeline"]["signal_recent_window_minutes"]
    recent_count = count_signals_for_run(run_id=run_id, minutes=recent_window)
    if recent_count >= 3:
        logger.info("Run %s already has %d signals. Skipping fallback.", run_id, recent_count)
        return recent_count

    success_count = 0
    for entry in build_signal_fallback_entries(report_content):
        result = write_signal(
            insight_type=entry["insight_type"],
            learning_content=entry["learning_content"],
            run_id=run_id,
        )
        if "✅" in result:
            success_count += 1
    return success_count


def run_obsidian_intelligence_system() -> dict:
    service = ObsidianPipelineService(repository=DatabaseTool())
    result = service.run_pipeline_sync()
    logger.info("Obsidian pipeline completed: %s", result["report_path"])
    return result


if __name__ == "__main__":
    try:
        run_obsidian_intelligence_system()
    except Exception as exc:
        logger.error("Pipeline failed: %s", exc)
        sys.exit(1)
