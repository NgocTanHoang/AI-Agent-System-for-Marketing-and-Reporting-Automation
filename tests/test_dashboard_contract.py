from src.init_db import init_db
from src.obsidian.pipeline import ObsidianPipelineService
from src.obsidian.repository import DatabaseTool


def test_dashboard_data_matches_contract(tmp_path, monkeypatch):
    db_path = tmp_path / "marketing.db"
    processed_dir = tmp_path / "processed"
    processed_dir.mkdir()
    init_db(str(db_path))
    monkeypatch.setenv("ENABLE_MOCK_LLM", "true")
    monkeypatch.setenv("DDGS_ENABLED", "false")

    service = ObsidianPipelineService(repository=DatabaseTool(db_path=db_path, processed_dir=processed_dir))
    service.run_pipeline_sync(run_id="dash001")
    dashboard = service.get_dashboard_data("dash001")

    assert set(dashboard.keys()) == {
        "kpi_cards",
        "charts",
        "agent_status",
        "insights",
        "recommendations",
        "last_run",
    }
    assert set(dashboard["charts"].keys()) == {
        "revenue_by_campaign",
        "product_sales_ranking",
        "campaign_roi",
        "sales_trend",
        "conversion_funnel",
        "product_matrix",
        "channel_performance",
    }
    assert dashboard["last_run"]["run_id"] == "dash001"
    assert dashboard["last_run"]["status"] == "COMPLETED"
    assert dashboard["last_run"]["completed_at"] is not None
    assert dashboard["last_run"]["report_path"]
    for chart in dashboard["charts"].values():
        assert "labels" in chart
        assert "datasets" in chart
