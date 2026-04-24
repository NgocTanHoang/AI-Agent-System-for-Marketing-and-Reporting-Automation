from fastapi.testclient import TestClient

import app as app_module
import src.runtime_data as runtime_data
from src.init_db import init_db


def test_dashboard_endpoints_keep_response_shape(tmp_path, monkeypatch):
    db_path = tmp_path / "marketing.db"
    init_db(str(db_path))

    monkeypatch.setattr(app_module, "DATABASE_PATH", db_path)
    monkeypatch.setattr(runtime_data, "DATABASE_PATH", db_path)
    monkeypatch.setitem(app_module.SETTINGS["dashboard"], "social_post_limit", 2)

    client = TestClient(app_module.app)

    model_info = client.get("/api/model-info")
    social_posts = client.get("/api/social-posts")

    assert model_info.status_code == 200
    assert social_posts.status_code == 200
    assert "primary_model" in model_info.json()
    assert "backup_provider" in model_info.json()
    assert len(social_posts.json()["posts"]) == 2
