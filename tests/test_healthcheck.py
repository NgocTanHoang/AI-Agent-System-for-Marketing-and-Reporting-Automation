import infra.healthcheck as healthcheck


def test_worker_healthcheck_defaults_to_core_modules(monkeypatch):
    monkeypatch.delenv("HEALTHCHECK_REQUIRE_VECTOR_MODULES", raising=False)

    modules = healthcheck.get_required_modules("worker")

    assert "crewai" in modules
    assert "sentence_transformers" not in modules
    assert "torch" not in modules


def test_worker_healthcheck_can_require_vector_modules(monkeypatch):
    monkeypatch.setenv("HEALTHCHECK_REQUIRE_VECTOR_MODULES", "true")

    modules = healthcheck.get_required_modules("worker")

    assert "chromadb" in modules
    assert "sentence_transformers" in modules
    assert "torch" in modules
