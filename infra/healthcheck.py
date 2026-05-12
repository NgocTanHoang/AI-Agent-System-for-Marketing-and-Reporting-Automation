#!/usr/bin/env python3
"""Health checks for local/Docker runtime."""

from __future__ import annotations

import argparse
import importlib
import os
import sys
from datetime import datetime
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen


REQUIRED_DIRS = [
    Path("data/raw/marketing_content"),
    Path("data/processed"),
    Path("logs"),
]

REQUIRED_MODULES = [
    "crewai",
    "litellm",
    "pydantic",
    "dotenv",
    "pandas",
    "ddgs",
    "sentence_transformers",
    "matplotlib",
    "fastapi",
    "uvicorn",
    "markdown",
    "chromadb",
]


def check_required_directories() -> tuple[bool, str]:
    for directory in REQUIRED_DIRS:
        if not directory.exists() or not directory.is_dir():
            return False, f"Directory missing: {directory}"

        test_file = directory / ".write_test"
        try:
            test_file.touch()
            test_file.unlink()
        except OSError as exc:
            return False, f"Directory not writable: {directory} ({exc})"

    return True, "Directories are present and writable"


def check_required_modules() -> tuple[bool, list[str]]:
    missing = []
    for module_name in REQUIRED_MODULES:
        try:
            importlib.import_module(module_name)
        except ImportError:
            missing.append(module_name)
    return len(missing) == 0, missing


def check_health_endpoint(url: str) -> tuple[bool, str]:
    try:
        with urlopen(url, timeout=5) as response:
            if response.status != 200:
                return False, f"Health endpoint returned {response.status}"
            body = response.read().decode("utf-8", errors="ignore")
            if '"status"' not in body:
                return False, "Health endpoint response missing status field"
            return True, "Health endpoint reachable"
    except URLError as exc:
        return False, f"Health endpoint unreachable: {exc}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Health check for AI Marketing Agent System")
    parser.add_argument("--mode", choices=["web", "worker"], default=os.getenv("HEALTHCHECK_MODE", "web"))
    parser.add_argument(
        "--url",
        default=os.getenv("HEALTHCHECK_URL", "http://127.0.0.1:8000/api/health"),
        help="Health endpoint URL for web mode",
    )
    args = parser.parse_args()

    print(f"[{datetime.now().isoformat()}] Performing {args.mode} health check...")

    checks: list[tuple[str, bool, str]] = []

    dirs_ok, dirs_msg = check_required_directories()
    checks.append(("Directories", dirs_ok, dirs_msg))

    modules_ok, missing_modules = check_required_modules()
    checks.append(
        (
            "Python Modules",
            modules_ok,
            "All required modules available" if modules_ok else f"Missing modules: {missing_modules}",
        )
    )

    if args.mode == "web":
        health_ok, health_msg = check_health_endpoint(args.url)
        checks.append(("HTTP Health Endpoint", health_ok, health_msg))

    failures = [name for name, ok, _ in checks if not ok]
    for name, ok, message in checks:
        prefix = "OK" if ok else "ERROR"
        print(f"{prefix}: {name} - {message}")

    if failures:
        print(f"STATUS: UNHEALTHY ({', '.join(failures)})")
        return 1

    print("STATUS: HEALTHY")
    return 0


if __name__ == "__main__":
    sys.exit(main())
