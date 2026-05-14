from __future__ import annotations

import os
import threading
import time
from dataclasses import dataclass
from typing import Callable

from litellm import completion

from src.config import load_pipeline_settings


@dataclass
class LLMResponse:
    content: str
    provider: str
    model: str
    latency_ms: int
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None
    used_mock: bool = False
    error: str | None = None


class _RateLimiter:
    def __init__(self, rpm: int) -> None:
        self.rpm = rpm
        self.lock = threading.Lock()
        self.request_times: list[float] = []

    def acquire(self) -> None:
        with self.lock:
            now = time.time()
            window_start = now - 60
            self.request_times = [item for item in self.request_times if item >= window_start]
            if len(self.request_times) >= self.rpm:
                sleep_for = 60 - (now - self.request_times[0]) + 0.05
                if sleep_for > 0:
                    time.sleep(sleep_for)
            self.request_times.append(time.time())


class ModelRouterTool:
    def __init__(self) -> None:
        settings = load_pipeline_settings()
        self.primary = settings["llm"]["primary"]
        self.backup = settings["llm"]["backup"]
        self.primary_rpm = int(os.getenv("NVIDIA_RPM_LIMIT", "40"))
        self.mode_provider = os.getenv("MODEL_PROVIDER", "auto").lower()
        self.mock_mode = os.getenv("ENABLE_MOCK_LLM", "false").lower() in {"1", "true", "yes", "on"}
        self.rate_limiter = _RateLimiter(self.primary_rpm)

    def _providers(self) -> list[tuple[str, dict, str | None]]:
        primary_key = os.getenv("NVIDIA_NIM_API_KEY") or os.getenv("NVIDIA_API_KEY")
        backup_key = os.getenv("OPENROUTER_API_KEY")
        options = [
            ("nvidia", self.primary, primary_key),
            ("openrouter", self.backup, backup_key),
        ]
        if self.mode_provider == "openrouter":
            options.reverse()
        return options

    def complete(
        self,
        agent_name: str,
        system_prompt: str,
        user_prompt: str,
        fallback_builder: Callable[[], str],
    ) -> LLMResponse:
        if self.mock_mode:
            return LLMResponse(
                content=fallback_builder(),
                provider="mock",
                model="mock-rule-engine",
                latency_ms=0,
                used_mock=True,
            )

        errors: list[str] = []
        for provider_name, provider_config, api_key in self._providers():
            if not api_key:
                errors.append(f"{provider_name}: missing API key")
                continue

            start = time.perf_counter()
            try:
                if provider_name == "nvidia":
                    self.rate_limiter.acquire()
                response = completion(
                    model=provider_config["model_id"],
                    api_key=api_key,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    timeout=90,
                    temperature=0.2,
                    max_tokens=1800,
                )
                latency_ms = int((time.perf_counter() - start) * 1000)
                content = response["choices"][0]["message"]["content"]
                return LLMResponse(
                    content=content,
                    provider=provider_name,
                    model=provider_config["model_id"],
                    latency_ms=latency_ms,
                    prompt_tokens=(response.get("usage") or {}).get("prompt_tokens"),
                    completion_tokens=(response.get("usage") or {}).get("completion_tokens"),
                    total_tokens=(response.get("usage") or {}).get("total_tokens"),
                )
            except Exception as exc:  # pragma: no cover - exact provider failure varies
                errors.append(f"{provider_name}: {exc}")

        return LLMResponse(
            content=fallback_builder(),
            provider="fallback",
            model="deterministic-fallback",
            latency_ms=0,
            used_mock=True,
            error=" | ".join(errors) if errors else "No provider succeeded.",
        )
