import main as main_module


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
