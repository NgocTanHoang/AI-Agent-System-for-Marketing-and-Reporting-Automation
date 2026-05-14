from __future__ import annotations

from typing import Any

from src.obsidian.llm import LLMResponse, ModelRouterTool
from src.obsidian.schemas import Recommendation


class ObsidianAgents:
    AGENT_SEQUENCE = [
        "Data Analyst Agent",
        "Market Research Agent",
        "Campaign Performance Agent",
        "Product Strategy Agent",
        "Insight Synthesizer Agent",
        "Report Writer Agent",
    ]

    def __init__(self, router: ModelRouterTool) -> None:
        self.router = router

    def _complete(self, agent_name: str, system_prompt: str, user_prompt: str, fallback: str) -> LLMResponse:
        return self.router.complete(
            agent_name=agent_name,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            fallback_builder=lambda: fallback,
        )

    def run_data_analyst(self, metrics: dict[str, Any]) -> LLMResponse:
        fallback = (
            f"Revenue is {metrics['revenue']:,.0f} VND across {metrics['units_sold']:,} units. "
            f"ROAS is {metrics['ROAS']:.2f}x and ROI is {metrics['ROI']:.2f}x. "
            f"{metrics['best_selling_product']['name']} leads volume while {metrics['worst_selling_product']['name']} trails."
        )
        return self._complete(
            "Data Analyst Agent",
            "You explain deterministic KPI outputs for a marketing leadership audience. Respond in English only, preserve numeric values exactly, and never convert VND to USD or any other currency. Do not invent missing metrics.",
            f"Explain these KPI outputs in 4 concise sentences. Keep currency labels in VND exactly as provided: {metrics}",
            fallback,
        )

    def run_market_research(self, topic: str, search_results: list[dict[str, Any]]) -> LLMResponse:
        if search_results:
            references = "\n".join(
                f"- {item['title']} | {item['url']} | {item['snippet']} | {item['retrieved_at']}"
                for item in search_results[:5]
            )
            fallback = "Technology signals emphasize AI-led smartphone differentiation, battery efficiency, and camera performance, based on the retrieved DDGS sources."
        else:
            references = "No DDGS search results were available."
            fallback = "Market research is limited because DDGS did not return results. Use internal KPI trends and rerun with DDGS enabled."

        return self._complete(
            "Market Research Agent",
            "You summarize market and technology search results. Respond in English only with 3-5 bullet points. Every bullet must be grounded in the provided sources. Never invent sources and always mention if no source data exists.",
            f"Topic: {topic}\nSearch results:\n{references}\nProvide a concise market signal summary in English bullet points, and keep source facts attributable.",
            fallback,
        )

    def run_campaign_performance(self, metrics: dict[str, Any]) -> LLMResponse:
        best = metrics["best_campaign"] or {}
        worst = metrics["worst_campaign"] or {}
        fallback = (
            f"{best.get('campaign_name', 'No campaign')} is the strongest campaign with success score {best.get('campaign_success_score', 0)} "
            f"and ROI {best.get('roi', 0)}. {worst.get('campaign_name', 'No campaign')} is the weakest and should be reviewed for budget efficiency."
        )
        return self._complete(
            "Campaign Performance Agent",
            "You evaluate marketing campaign performance using deterministic ROI, ROAS, conversion, and cost metrics. Respond in English only and preserve all numeric values exactly as provided.",
            f"Metrics: {metrics}\nExplain best and worst campaign performance with cost discipline. Do not convert any VND values to other currencies.",
            fallback,
        )

    def run_product_strategy(self, metrics: dict[str, Any]) -> LLMResponse:
        fallback = (
            f"Prioritize {metrics['best_selling_product']['name']} as the hero product and investigate low demand for "
            f"{metrics['worst_selling_product']['name']}. {metrics['product_focus_recommendation']}"
        )
        return self._complete(
            "Product Strategy Agent",
            "You identify product focus priorities using deterministic sales metrics. Respond in English only and preserve all numeric values exactly as provided.",
            f"Metrics: {metrics}\nRecommend product focus and remediation priorities. Do not convert any VND values to other currencies.",
            fallback,
        )

    def run_insight_synthesizer(
        self,
        metrics: dict[str, Any],
        data_summary: str,
        market_summary: str,
        campaign_summary: str,
        product_summary: str,
    ) -> LLMResponse:
        fallback = (
            f"Internal performance points to {metrics['best_selling_product']['name']} as the strongest growth lever, while "
            f"campaign optimization should follow the highest success-score channel. Market signals reinforce the need to message AI capability and camera value clearly."
        )
        return self._complete(
            "Insight Synthesizer Agent",
            "You synthesize database facts and market research into strategic conclusions for product and campaign planning. Respond in English only and preserve KPI values and currency units exactly.",
            (
                f"Metrics: {metrics}\n"
                f"Data Analyst: {data_summary}\n"
                f"Market Research: {market_summary}\n"
                f"Campaign Performance: {campaign_summary}\n"
                f"Product Strategy: {product_summary}\n"
                "Create a strategic conclusion in 4-6 sentences. Do not convert any VND values to other currencies."
            ),
            fallback,
        )

    def build_recommendations(self, metrics: dict[str, Any]) -> list[Recommendation]:
        best_campaign = metrics["best_campaign"] or {}
        return [
            Recommendation(
                campaign_name="Obsidian AI Upgrade Sprint",
                target_audience="Performance-focused Millennials and upper-mass Gen Z buyers",
                product_focus=metrics["best_selling_product"]["name"],
                channel=best_campaign.get("channel", "TikTok"),
                budget_suggestion=f"Reallocate 15-20% of spend toward {best_campaign.get('channel', 'the top ROI channel')}",
                kpi_target=f"ROAS > {max((metrics['ROAS'] or 0) * 1.1, 1):.2f}x and conversion rate > {max((metrics['conversion_rate'] or 0) * 1.05, 0):.2%}",
                rationale="The best-selling SKU already has demand momentum, so campaign budget should amplify an asset with proven pull.",
                risk="If inventory or creative fatigue is already high, the incremental spend may hit diminishing returns.",
            ),
            Recommendation(
                campaign_name="Obsidian Recovery Playbook",
                target_audience="Price-sensitive mainstream buyers in underperforming segments",
                product_focus=metrics["worst_selling_product"]["name"],
                channel="Meta + search retargeting",
                budget_suggestion="Use a tightly controlled test budget with bundle or financing offers",
                kpi_target="Lift units sold by at least 15% without letting CPA rise above the current blended average",
                rationale="The weakest SKU needs a focused test rather than broad spend, using pricing and landing-page refinement to confirm whether the issue is offer, message, or audience.",
                risk="If the product-market fit is structurally weak, even a controlled test may not recover demand.",
            ),
        ]
