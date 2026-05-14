from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
REQUIRED_SECTIONS = [
    "## 1. Executive Summary",
    "## 2. Data Sources",
    "## 3. Campaign Performance Overview",
    "## 4. Product Performance Analysis",
    "## 5. Market & Technology Signals",
    "## 6. Key Charts Interpretation",
    "## 7. Strategic Insights",
    "## 8. Recommended Campaigns",
    "## 9. Product Focus Plan",
    "## 10. Risks & Limitations",
    "## 11. Next Actions",
]


def require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise SystemExit(f"Missing required environment variable: {name}")
    return value


def http_json(url: str, method: str = "GET", payload: dict | None = None) -> dict:
    data = None
    headers = {"Content-Type": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
    request = Request(url, data=data, headers=headers, method=method)
    try:
        with urlopen(request, timeout=120) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"HTTP {exc.code} for {url}: {body}") from exc
    except URLError as exc:
        raise SystemExit(f"Cannot reach {url}: {exc}") from exc


def emit_json(payload: dict) -> None:
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    sys.stdout.buffer.write((text + "\n").encode("utf-8"))


def assert_dashboard_contract(dashboard: dict) -> None:
    required = {"kpi_cards", "charts", "agent_status", "insights", "recommendations", "last_run"}
    missing = required - set(dashboard.keys())
    if missing:
        raise SystemExit(f"Dashboard contract missing keys: {sorted(missing)}")
    for name, chart in dashboard["charts"].items():
        if "labels" not in chart or "datasets" not in chart:
            raise SystemExit(f"Chart contract invalid for {name}")


def report_market_signal_count(report_content: str) -> int:
    section = report_content.split("## 5. Market & Technology Signals", 1)
    if len(section) < 2:
        return 0
    lines = []
    for line in section[1].splitlines()[1:]:
        if line.startswith("## "):
            break
        if line.strip():
            lines.append(line.strip())
    return sum(1 for line in lines if line.startswith("- "))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--timeout-seconds", type=int, default=420)
    args = parser.parse_args()

    load_dotenv(PROJECT_ROOT / ".env")
    require_env("NVIDIA_API_KEY")
    require_env("OPENROUTER_API_KEY")
    if os.getenv("ENABLE_MOCK_LLM", "").lower() in {"1", "true", "yes", "on"}:
        raise SystemExit("ENABLE_MOCK_LLM must be false for live API smoke.")

    base = args.base_url.rstrip("/") + "/"
    health = http_json(urljoin(base, "api/health"))
    run = http_json(urljoin(base, "api/run-pipeline"), method="POST", payload={})
    run_id = run["run_id"]

    deadline = time.time() + args.timeout_seconds
    status = {}
    while time.time() < deadline:
        status = http_json(urljoin(base, "api/pipeline-status"))
        if status.get("status") in {"COMPLETED", "FAILED"}:
            break
        time.sleep(3)
    if status.get("status") != "COMPLETED":
        raise SystemExit(f"Pipeline did not complete successfully: {status}")

    logs = http_json(urljoin(base, f"api/agent-logs?run_id={run_id}"))
    dashboard = http_json(urljoin(base, "api/dashboard-data"))
    reports = http_json(urljoin(base, "api/reports"))
    latest_id = reports["reports"][0]["id"]
    report = http_json(urljoin(base, f"api/report/{latest_id}"))

    assert_dashboard_contract(dashboard)
    for section in REQUIRED_SECTIONS:
        if section not in report["content"]:
            raise SystemExit(f"Missing report section: {section}")

    live_agents = []
    for agent in status.get("agent_status", []):
        if agent.get("provider") in {"nvidia", "openrouter"}:
            live_agents.append(agent["name"])
    if not live_agents:
        raise SystemExit("No live provider was used by any agent.")

    signal_count = report_market_signal_count(report["content"])
    if signal_count < 3:
        raise SystemExit(f"Expected at least 3 web market signals in report, got {signal_count}")

    payload = {
        "health": {
            "status": health.get("status"),
            "mock_mode": health.get("mock_mode"),
            "llm_credentials_available": health.get("llm_credentials_available"),
        },
        "run": run,
        "status": status,
        "live_agents": live_agents,
        "dashboard_summary": {
            "kpi_count": len(dashboard["kpi_cards"]),
            "chart_names": sorted(dashboard["charts"].keys()),
            "recommendation_count": len(dashboard["recommendations"]),
            "last_run": dashboard["last_run"],
        },
        "latest_report": {
            "id": latest_id,
            "filename": report["filename"],
            "market_signal_bullets": signal_count,
        },
        "agent_logs_count": len(logs.get("logs", [])),
    }
    emit_json(payload)


if __name__ == "__main__":
    main()
