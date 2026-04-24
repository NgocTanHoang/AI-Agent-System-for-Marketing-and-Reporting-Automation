import os

from src.config import get_runtime_model_info, load_pipeline_settings


def test_load_pipeline_settings_merges_overrides(tmp_path):
    config_path = tmp_path / "pipeline.json"
    config_path.write_text(
        """
        {
          "pipeline": {
            "market_topic": "custom topic",
            "feedback_signal_limit": 2
          },
          "analysis": {
            "allowed_regions": ["North", "South"]
          }
        }
        """,
        encoding="utf-8",
    )

    settings = load_pipeline_settings(config_path)

    assert settings["pipeline"]["market_topic"] == "custom topic"
    assert settings["pipeline"]["feedback_signal_limit"] == 2
    assert settings["pipeline"]["report_prefix"] == "Smartphone_Strategic_Report"
    assert settings["analysis"]["allowed_regions"] == ["North", "South"]


def test_runtime_model_info_reflects_available_credentials(monkeypatch):
    monkeypatch.delenv("NVIDIA_NIM_API_KEY", raising=False)
    monkeypatch.delenv("NVIDIA_API_KEY", raising=False)
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-openrouter")

    info = get_runtime_model_info()

    assert info["primary_model"]["api_connected"] is False
    assert info["backup_provider"]["api_connected"] is True
    assert info["orchestrator"]["agents"]
