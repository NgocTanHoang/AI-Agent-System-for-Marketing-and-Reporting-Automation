import main as main_module
from src.reporting import missing_required_sections


def test_ensure_signal_updates_uses_current_run_id(monkeypatch):
    captured = []

    monkeypatch.setattr(main_module, "load_pipeline_settings", lambda: {
        "pipeline": {"signal_recent_window_minutes": 10}
    })
    monkeypatch.setattr(main_module, "count_signals_for_run", lambda run_id, minutes: 0)
    monkeypatch.setattr(
        main_module,
        "build_signal_fallback_entries",
        lambda report_content, db_path=None: [
            {"insight_type": "low_performer", "learning_content": "lp"},
            {"insight_type": "budget_realloc", "learning_content": "br"},
            {"insight_type": "trend_alert", "learning_content": "ta"},
        ],
    )
    monkeypatch.setattr(
        main_module,
        "write_signal",
        lambda insight_type, learning_content, run_id="": captured.append(
            (insight_type, learning_content, run_id)
        ) or "✅ ok",
    )

    main_module._ensure_signal_updates("demo report", run_id="run-123")

    assert len(captured) == 3
    assert {entry[0] for entry in captured} == {
        "low_performer",
        "budget_realloc",
        "trend_alert",
    }
    assert all(entry[2] == "run-123" for entry in captured)


def test_ensure_signal_updates_skips_when_current_run_already_has_signals(monkeypatch):
    monkeypatch.setattr(main_module, "load_pipeline_settings", lambda: {
        "pipeline": {"signal_recent_window_minutes": 10}
    })
    monkeypatch.setattr(main_module, "count_signals_for_run", lambda run_id, minutes: 3)

    called = {"fallback": False}
    monkeypatch.setattr(
        main_module,
        "build_signal_fallback_entries",
        lambda report_content, db_path=None: called.__setitem__("fallback", True),
    )

    main_module._ensure_signal_updates("demo report", run_id="run-123")

    assert called["fallback"] is False


def test_mock_pipeline_generates_structured_report(monkeypatch, tmp_path):
    report_text = """# Marketing Intelligence Report

## 1. Executive Summary
Tom tat chien luoc.
## 2. Campaign Objective
Muc tieu campaign.
## 3. Target Audience
Chan dung khach hang.
## 4. Market & Competitor Insights
Thong tin thi truong.
## 5. Key Findings
Phat hien chinh.
## 6. Strategic Recommendations
De xuat chien luoc.
## 7. Content Plan
Ke hoach noi dung.
## 8. Channel Strategy
Chien luoc kenh.
## 9. KPI & Measurement Plan
Chi so do luong.
## 10. Risks & Mitigations
Rui ro va cach giam thieu.
## 11. Next Actions
Buoc tiep theo.
"""

    class FakeOutput:
        def __init__(self, raw):
            self.raw = raw

    class FakeTask:
        def __init__(self, kind):
            self.kind = kind
            self.output = None
            self.output_file = None

    class FakeAgent:
        def __init__(self):
            self.tools = []

    class FakeAgents:
        def search_analyst(self):
            return FakeAgent()

        def creative_director(self):
            return FakeAgent()

        def content_strategist(self):
            return FakeAgent()

        def business_reporter(self):
            return FakeAgent()

        def quality_assurance_agent(self):
            return FakeAgent()

    class FakeTasks:
        def research_task(self, **kwargs):
            return FakeTask("research")

        def creative_decision_task(self, **kwargs):
            return FakeTask("creative")

        def content_creation_task(self, **kwargs):
            return FakeTask("content")

        def data_fetch_task(self, **kwargs):
            return FakeTask("data")

        def marketing_strategy_task(self, **kwargs):
            return FakeTask("report")

        def signal_update_task(self, **kwargs):
            return FakeTask("signal")

        def qa_task(self, *args, **kwargs):
            return FakeTask("qa")

        def refine_report_task(self, *args, **kwargs):
            return FakeTask("refine")

    class FakeCrew:
        def __init__(self, agents=None, tasks=None, **kwargs):
            self.tasks = tasks or []

        def kickoff(self):
            if len(self.tasks) == 1 and self.tasks[0].kind == "qa":
                return FakeOutput("PASSED")

            report_task = next((task for task in self.tasks if task.kind == "report"), None)
            data_task = next((task for task in self.tasks if task.kind == "data"), None)
            if report_task:
                report_task.output = FakeOutput(report_text)
            if data_task:
                data_task.output = FakeOutput("mock sql rows")
            return FakeOutput(report_text)

    monkeypatch.setattr(main_module, "validate_config", lambda: None)
    monkeypatch.setattr(main_module, "load_pipeline_settings", lambda: {
        "pipeline": {
            "market_topic": "demo topic",
            "feedback_signal_limit": 5,
            "feedback_lookback_days": 30,
            "signal_recent_window_minutes": 10,
            "report_prefix": "Test_Report",
        },
        "analysis": {"allowed_regions": ["North", "South", "Central", "Highlands"]},
    })
    monkeypatch.setattr(main_module, "build_memory_context", lambda **kwargs: "")
    monkeypatch.setattr(main_module, "build_channel_roi_reference", lambda settings=None: "TikTok=1.0")
    monkeypatch.setattr(main_module, "format_regions", lambda settings=None: "North, South, Central, Highlands")
    monkeypatch.setattr(main_module, "MarketingAgents", FakeAgents)
    monkeypatch.setattr(main_module, "MarketingTasks", FakeTasks)
    monkeypatch.setattr(main_module, "Crew", FakeCrew)
    monkeypatch.setattr(main_module, "_ensure_signal_updates", lambda *args, **kwargs: None)
    monkeypatch.setattr(main_module, "log_run", lambda **kwargs: None)
    monkeypatch.setattr(main_module, "PROCESSED_DATA_DIR", tmp_path)

    result = main_module.run_smartphone_intelligence_system()

    saved_reports = list(tmp_path.glob("Test_Report_*.md"))
    assert result is not None
    assert len(saved_reports) == 1
    assert missing_required_sections(saved_reports[0].read_text(encoding="utf-8")) == []
