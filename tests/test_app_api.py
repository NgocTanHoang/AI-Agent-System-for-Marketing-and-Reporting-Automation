from fastapi.testclient import TestClient

import app as app_module
from src.init_db import init_db
from src.obsidian.pipeline import ObsidianPipelineService
from src.obsidian.repository import DatabaseTool


def build_test_service(tmp_path, monkeypatch):
    db_path = tmp_path / "marketing.db"
    processed_dir = tmp_path / "processed"
    processed_dir.mkdir()
    init_db(str(db_path))
    monkeypatch.setenv("ENABLE_MOCK_LLM", "true")
    monkeypatch.setenv("DDGS_ENABLED", "false")
    repo = DatabaseTool(db_path=db_path, processed_dir=processed_dir)
    service = ObsidianPipelineService(repository=repo)
    monkeypatch.setattr(app_module, "DATABASE_PATH", db_path)
    monkeypatch.setattr(app_module, "PROCESSED_DATA_DIR", processed_dir)
    monkeypatch.setattr(app_module, "REPOSITORY", repo)
    monkeypatch.setattr(app_module, "PIPELINE", service)
    return service


def test_obsidian_api_endpoints(tmp_path, monkeypatch):
    service = build_test_service(tmp_path, monkeypatch)
    result = service.run_pipeline_sync(run_id="apitest01")

    client = TestClient(app_module.app)
    health = client.get("/api/health")
    status = client.get("/api/pipeline-status")
    dashboard = client.get("/api/dashboard-data")
    reports = client.get("/api/reports")
    logs = client.get("/api/agent-logs")
    report = client.get(f"/api/report/{reports.json()['reports'][0]['id']}")

    assert health.status_code == 200
    assert status.status_code == 200
    assert dashboard.status_code == 200
    assert reports.status_code == 200
    assert logs.status_code == 200
    assert report.status_code == 200
    assert status.json()["status"] == "COMPLETED"
    assert dashboard.json()["last_run"]["run_id"] == "apitest01"
    assert "kpi_cards" in dashboard.json()
    assert reports.json()["reports"][0]["filename"].endswith(".md")
    assert report.json()["content"].startswith("# Obsidian Intelligence Report")
    assert result["status"] == "COMPLETED"


def test_run_pipeline_endpoint_returns_queued(tmp_path, monkeypatch):
    service = build_test_service(tmp_path, monkeypatch)
    monkeypatch.setattr(service, "run_pipeline_async", lambda: {"run_id": "queued001", "status": "queued"})

    client = TestClient(app_module.app)
    response = client.post("/api/run-pipeline", json={"force": False})

    assert response.status_code == 202
    assert response.json()["run_id"] == "queued001"
    assert response.json()["status"] == "queued"
