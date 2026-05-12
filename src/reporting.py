"""Helpers for validating report structure without mutating report content."""

from __future__ import annotations

import re

REQUIRED_REPORT_SECTIONS = [
    "Executive Summary",
    "Campaign Objective",
    "Target Audience",
    "Market & Competitor Insights",
    "Key Findings",
    "Strategic Recommendations",
    "Content Plan",
    "Channel Strategy",
    "KPI & Measurement Plan",
    "Risks & Mitigations",
    "Next Actions",
]


def _normalize_heading(heading: str) -> str:
    normalized = heading.strip().lower()
    normalized = re.sub(r"^\d+[\.\)]\s*", "", normalized)
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized


def extract_markdown_headings(content: str) -> list[str]:
    return [match.group(1).strip() for match in re.finditer(r"^##\s+(.*)$", content, flags=re.MULTILINE)]


def missing_required_sections(content: str) -> list[str]:
    headings = {_normalize_heading(item) for item in extract_markdown_headings(content)}
    missing = []
    for section in REQUIRED_REPORT_SECTIONS:
        if _normalize_heading(section) not in headings:
            missing.append(section)
    return missing
