from __future__ import annotations

import os
from datetime import date
from typing import Any

from ddgs import DDGS


class DDGSSearchTool:
    def __init__(self) -> None:
        self.enabled = os.getenv("DDGS_ENABLED", "true").lower() in {"1", "true", "yes", "on"}

    def search(self, query: str, max_results: int = 5) -> list[dict[str, Any]]:
        if not self.enabled:
            return []

        try:
            with DDGS() as client:
                results = list(client.text(query, max_results=max_results))
        except Exception:
            return []

        output = []
        retrieved_at = str(date.today())
        for item in results:
            output.append(
                {
                    "title": item.get("title", "").strip(),
                    "url": item.get("href", "").strip(),
                    "snippet": item.get("body", "").strip(),
                    "retrieved_at": retrieved_at,
                }
            )
        return output

