import main as main_module
from src.init_db import init_db
from src.obsidian.pipeline import ObsidianPipelineService
from src.obsidian.repository import DatabaseTool


def test_ensure_signal_updates_uses_current_run_id(monkeypatch):
    captured = []

    monkeypatch.setattr(main_module, "load_pipeline_settings", lambda: {
        "pipeline": {"signal_recent_window_minutes": 10}
    })
    monkeypatch.setattr(main_module, "count_signals_for_run", lambda run_id, minutes: 0)
    monkeypatch.setattr(
        main_module,
        "build_signal_fallback_entries",
        lambda report_content: [
            {"insight_type": "low_performer", "learning_content": "lp"},
            {"insight_type": "budget_realloc", "learning_content": "br"},
            {"insight_type": "trend_alert", "learning_content": "ta"},
        ],
    )
    monkeypatch.setattr(
        main_module,
        "write_signal",
        lambda insight_type, learning_content, run_id="": captured.append((insight_type, learning_content, run_id)) or "✅ ok",
    )

    assert main_module._ensure_signal_updates("demo", run_id="run-123") == 3
    assert all(item[2] == "run-123" for item in captured)


def test_mock_pipeline_generates_obsidian_report(tmp_path, monkeypatch):
    db_path = tmp_path / "marketing.db"
    processed_dir = tmp_path / "processed"
    processed_dir.mkdir()
    init_db(str(db_path))

    monkeypatch.setenv("ENABLE_MOCK_LLM", "true")
    monkeypatch.setenv("DDGS_ENABLED", "false")

    service = ObsidianPipelineService(repository=DatabaseTool(db_path=db_path, processed_dir=processed_dir))
    result = service.run_pipeline_sync(run_id="mockrun1")

    report_path = processed_dir / [item.name for item in processed_dir.glob("Obsidian_Intelligence_Report_*.md")][0]
    report = report_path.read_text(encoding="utf-8")

    assert result["status"] == "COMPLETED"
    assert "## 1. Executive Summary" in report
    assert "## 11. Next Actions" in report
