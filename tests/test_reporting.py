from src.reporting import extract_markdown_headings, missing_required_sections


def test_report_contract_detects_complete_structure():
    report = """
# Marketing Intelligence Report

## 1. Executive Summary
## 2. Campaign Objective
## 3. Target Audience
## 4. Market & Competitor Insights
## 5. Key Findings
## 6. Strategic Recommendations
## 7. Content Plan
## 8. Channel Strategy
## 9. KPI & Measurement Plan
## 10. Risks & Mitigations
## 11. Next Actions
"""

    assert len(extract_markdown_headings(report)) == 11
    assert missing_required_sections(report) == []


def test_report_contract_reports_missing_sections():
    report = """
# Marketing Intelligence Report

## 1. Executive Summary
## 2. Campaign Objective
## 3. Target Audience
"""

    missing = missing_required_sections(report)

    assert "Key Findings" in missing
    assert "Next Actions" in missing
