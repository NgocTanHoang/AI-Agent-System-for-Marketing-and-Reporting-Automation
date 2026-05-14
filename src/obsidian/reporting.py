from __future__ import annotations

from typing import Any

from src.obsidian.schemas import Recommendation


def format_currency(value: float | int | None) -> str:
    if value is None:
        return "Unavailable"
    return f"{value:,.0f} VND"


class ReportExportTool:
    def build_report(
        self,
        run_id: str,
        metrics: dict[str, Any],
        agent_outputs: dict[str, str],
        search_results: list[dict[str, Any]],
        recommendations: list[Recommendation],
    ) -> str:
        lines = [
            "# Obsidian Intelligence Report",
            "",
            "## 1. Executive Summary",
            agent_outputs["Insight Synthesizer Agent"],
            "",
            "## 2. Data Sources",
            "- SQLite marketing database: sales, marketing_campaigns, social_sentiment, competitor_products, sales_performance",
            f"- Pipeline run id: `{run_id}`",
            f"- DDGS results retrieved: {len(search_results)}",
            "",
            "## 3. Campaign Performance Overview",
            agent_outputs["Campaign Performance Agent"],
            "",
            "## 4. Product Performance Analysis",
            agent_outputs["Product Strategy Agent"],
            "",
            "## 5. Market & Technology Signals",
            agent_outputs["Market Research Agent"],
            "",
            "## 6. Key Charts Interpretation",
            agent_outputs["Data Analyst Agent"],
            "",
            "## 7. Strategic Insights",
            agent_outputs["Insight Synthesizer Agent"],
            "",
            "## 8. Recommended Campaigns",
        ]

        for recommendation in recommendations:
            lines.extend(
                [
                    f"### {recommendation.campaign_name}",
                    f"- Target audience: {recommendation.target_audience}",
                    f"- Product focus: {recommendation.product_focus}",
                    f"- Channel: {recommendation.channel}",
                    f"- Budget suggestion: {recommendation.budget_suggestion}",
                    f"- KPI target: {recommendation.kpi_target}",
                    f"- Rationale: {recommendation.rationale}",
                    f"- Risk: {recommendation.risk}",
                    "",
                ]
            )

        lines.extend(
            [
                "## 9. Product Focus Plan",
                metrics["product_focus_recommendation"],
                "",
                "## 10. Risks & Limitations",
                "- CTR and CPC are unavailable because the current schema does not include click/impression fields.",
                f"- Profit is computed as revenue minus total marketing spend ({format_currency(metrics['total_marketing_spend'])}); product cost of goods is not available.",
                "- Market research depends on DDGS and may return fewer signals if the search provider throttles or the network is unavailable.",
                "",
                "## 11. Next Actions",
                "- Review the latest dashboard and validate whether the top recommendation aligns with channel capacity and inventory.",
                "- Add click/impression fields to the campaign schema if CTR/CPC must become first-class metrics.",
                "- Re-run the pipeline after the next campaign batch lands in the database to update market signals and KPI movement.",
            ]
        )

        if search_results:
            lines.extend(["", "### DDGS Source Notes"])
            for item in search_results[:5]:
                lines.append(f"- [{item['title']}]({item['url']}) — retrieved {item['retrieved_at']}")

        return "\n".join(lines)

