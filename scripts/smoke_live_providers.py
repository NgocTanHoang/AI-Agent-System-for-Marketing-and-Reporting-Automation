from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import load_pipeline_settings
from src.obsidian.llm import ModelRouterTool
from src.obsidian.search import DDGSSearchTool


def require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise SystemExit(f"Missing required environment variable: {name}")
    return value


def mask(value: str) -> str:
    if len(value) < 10:
        return "***"
    return f"{value[:4]}...{value[-4:]}"


def emit_json(payload: dict) -> None:
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    sys.stdout.buffer.write((text + "\n").encode("utf-8"))


def provider_smoke(mode: str, force_missing_nvidia: bool) -> dict:
    settings = load_pipeline_settings()
    original_provider = os.getenv("MODEL_PROVIDER")
    original_mock = os.getenv("ENABLE_MOCK_LLM")
    original_nvidia = os.getenv("NVIDIA_API_KEY")
    original_nvidia_nim = os.getenv("NVIDIA_NIM_API_KEY")
    try:
        os.environ["ENABLE_MOCK_LLM"] = "false"
        os.environ["MODEL_PROVIDER"] = mode
        if force_missing_nvidia:
            os.environ.pop("NVIDIA_API_KEY", None)
            os.environ.pop("NVIDIA_NIM_API_KEY", None)

        router = ModelRouterTool()
        response = router.complete(
            agent_name="Provider Smoke",
            system_prompt="You are a concise assistant. Reply with one sentence confirming the active provider.",
            user_prompt="Return JSON with keys provider_confirmation and summary. Keep it brief.",
            fallback_builder=lambda: "fallback should not be used during live provider smoke",
        )
        return {
            "requested_mode": mode,
            "forced_missing_nvidia": force_missing_nvidia,
            "provider": response.provider,
            "model": response.model,
            "latency_ms": response.latency_ms,
            "prompt_tokens": response.prompt_tokens,
            "completion_tokens": response.completion_tokens,
            "total_tokens": response.total_tokens,
            "used_mock": response.used_mock,
            "error": response.error,
            "content_preview": response.content[:300],
            "primary_model": settings["llm"]["primary"]["model_id"],
            "backup_model": settings["llm"]["backup"]["model_id"],
        }
    finally:
        if original_provider is None:
            os.environ.pop("MODEL_PROVIDER", None)
        else:
            os.environ["MODEL_PROVIDER"] = original_provider
        if original_mock is None:
            os.environ.pop("ENABLE_MOCK_LLM", None)
        else:
            os.environ["ENABLE_MOCK_LLM"] = original_mock
        if original_nvidia is None:
            os.environ.pop("NVIDIA_API_KEY", None)
        else:
            os.environ["NVIDIA_API_KEY"] = original_nvidia
        if original_nvidia_nim is None:
            os.environ.pop("NVIDIA_NIM_API_KEY", None)
        else:
            os.environ["NVIDIA_NIM_API_KEY"] = original_nvidia_nim


def ddgs_smoke() -> dict:
    original_ddgs = os.getenv("DDGS_ENABLED")
    try:
        os.environ["DDGS_ENABLED"] = "true"
        tool = DDGSSearchTool()
        queries = [
            "smartphone AI marketing trends 2026",
            "mobile campaign performance benchmarks 2026",
            "consumer electronics launch strategy AI features",
        ]
        results = {}
        for query in queries:
            items = tool.search(query, max_results=3)
            results[query] = [
                {
                    "title": item.get("title"),
                    "url": item.get("url"),
                    "snippet": item.get("snippet"),
                    "retrieved_at": item.get("retrieved_at"),
                }
                for item in items
            ]
        return results
    finally:
        if original_ddgs is None:
            os.environ.pop("DDGS_ENABLED", None)
        else:
            os.environ["DDGS_ENABLED"] = original_ddgs


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["auto", "openrouter"], default="auto")
    parser.add_argument("--force-openrouter-fallback", action="store_true")
    args = parser.parse_args()

    load_dotenv(PROJECT_ROOT / ".env")
    require_env("OPENROUTER_API_KEY")
    if not args.force_openrouter_fallback:
        require_env("NVIDIA_API_KEY")

    payload = {
        "env": {
            "ENABLE_MOCK_LLM": "false",
            "DDGS_ENABLED": os.getenv("DDGS_ENABLED", ""),
            "MODEL_PROVIDER": args.mode,
            "NVIDIA_API_KEY": mask(os.getenv("NVIDIA_API_KEY", "")) if os.getenv("NVIDIA_API_KEY") else None,
            "OPENROUTER_API_KEY": mask(os.getenv("OPENROUTER_API_KEY", "")),
        },
        "provider_smoke": provider_smoke(
            mode=args.mode,
            force_missing_nvidia=args.force_openrouter_fallback,
        ),
        "ddgs_smoke": ddgs_smoke(),
    }

    emit_json(payload)

    provider_result = payload["provider_smoke"]
    if provider_result["provider"] in {"fallback", "mock"}:
        raise SystemExit("Live provider smoke failed: router returned non-live fallback.")


if __name__ == "__main__":
    main()
