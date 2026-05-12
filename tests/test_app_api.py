from pathlib import Path

from fastapi.testclient import TestClient

import app as app_module
import src.runtime_data as runtime_data
from src.init_db import init_db


class _FakeProcess:
    def __init__(self, returncode=0, pid=4321):
        self.returncode = returncode
        self.pid = pid

    def wait(self):
        return self.returncode


def test_dashboard_endpoints_keep_response_shape(tmp_path, monkeypatch):
    db_path = tmp_path / "marketing.db"
    processed_dir = tmp_path / "processed"
    processed_dir.mkdir()
    (processed_dir / "sample.md").write_text(
        "# Marketing Intelligence Report\n\n## 1. Executive Summary\nNoi dung demo.",
        encoding="utf-8",
    )
    init_db(str(db_path))

    monkeypatch.setattr(app_module, "DATABASE_PATH", db_path)
    monkeypatch.setattr(app_module, "PROCESSED_DATA_DIR", processed_dir)
    monkeypatch.setattr(runtime_data, "DATABASE_PATH", db_path)
    monkeypatch.setitem(app_module.SETTINGS["dashboard"], "social_post_limit", 2)

    client = TestClient(app_module.app)

    health = client.get("/api/health")
    model_info = client.get("/api/model-info")
    social_posts = client.get("/api/social-posts")
    reports = client.get("/api/reports")
    report = client.get("/api/report/sample.md")

    assert health.status_code == 200
    assert health.json()["database_exists"] is True
    assert model_info.status_code == 200
    assert social_posts.status_code == 200
    assert reports.status_code == 200
    assert report.status_code == 200
    assert "primary_model" in model_info.json()
    assert "backup_provider" in model_info.json()
    assert len(social_posts.json()["posts"]) == 2
    assert reports.json()["reports"][0]["filename"] == "sample.md"
    assert report.json()["sections"][0]["heading"] == "Tổng quan"


def test_report_endpoint_blocks_path_traversal(tmp_path, monkeypatch):
    processed_dir = tmp_path / "processed"
    processed_dir.mkdir()
    monkeypatch.setattr(app_module, "PROCESSED_DATA_DIR", processed_dir)

    client = TestClient(app_module.app)
    response = client.get("/api/report/..%2Fsecret.md")

    assert response.status_code == 404


def test_run_endpoint_returns_started_and_updates_status(monkeypatch, tmp_path):
    log_file = tmp_path / "pipeline.log"
    monkeypatch.setattr(app_module, "LOG_FILE", log_file)
    monkeypatch.setattr(app_module, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(
        app_module.subprocess,
        "Popen",
        lambda *args, **kwargs: _FakeProcess(returncode=0, pid=5678),
    )
    app_module.PIPELINE_STATUS.update(
        {"status": "IDLE", "start_time": None, "end_time": None, "pid": None}
    )

    client = TestClient(app_module.app)
    response = client.post("/run")

    assert response.status_code == 202
    assert response.json()["status"] == "started"
    assert app_module.PIPELINE_STATUS["status"] == "COMPLETED"
    assert app_module.PIPELINE_STATUS["pid"] == 5678


def test_run_endpoint_rejects_when_already_running():
    app_module.PIPELINE_STATUS.update(
        {"status": "RUNNING", "start_time": None, "end_time": None, "pid": 99}
    )
    client = TestClient(app_module.app)

    response = client.post("/run")

    assert response.status_code == 409
    assert response.json()["status"] == "error"

    app_module.PIPELINE_STATUS.update(
        {"status": "IDLE", "start_time": None, "end_time": None, "pid": None}
    )
