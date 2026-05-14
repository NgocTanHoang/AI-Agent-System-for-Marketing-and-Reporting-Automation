from __future__ import annotations

from collections import defaultdict
from statistics import mean
from typing import Any


class MetricsTool:
    def compute(self, snapshot: dict[str, Any]) -> dict[str, Any]:
        sales = snapshot["sales"]
        campaigns = snapshot["campaigns"]
        campaign_sales = snapshot["campaign_sales"]
        performance = snapshot["performance"]

        total_revenue = float(sum(row["units_sold"] * row["unit_price"] for row in sales))
        total_units = int(sum(row["units_sold"] for row in sales))
        total_spend = float(sum(row["budget"] for row in campaigns))
        total_conversions = int(sum(row["conversions"] for row in campaigns))
        total_reach = int(sum(row["reach"] for row in campaigns))
        transactions = len(sales)
        profit = total_revenue - total_spend
        roas = (total_revenue / total_spend) if total_spend else None
        roi = (profit / total_spend) if total_spend else None
        conversion_rate = (total_conversions / total_reach) if total_reach else None
        cpa = (total_spend / total_conversions) if total_conversions else None
        aov = (total_revenue / transactions) if transactions else None

        product_units: dict[str, int] = defaultdict(int)
        product_revenue: dict[str, float] = defaultdict(float)
        for row in sales:
            product_units[row["model_name"]] += row["units_sold"]
            product_revenue[row["model_name"]] += row["units_sold"] * row["unit_price"]

        best_product = max(product_units.items(), key=lambda item: item[1]) if product_units else ("N/A", 0)
        worst_product = min(product_units.items(), key=lambda item: item[1]) if product_units else ("N/A", 0)

        max_roi = max((row["roi"] for row in campaigns), default=0) or 1
        max_conversions = max((row["conversions"] for row in campaigns), default=0) or 1
        max_reach = max((row["reach"] for row in campaigns), default=0) or 1

        scored_campaigns = []
        for row in campaigns:
            score = round(
                (
                    (max(row["roi"], 0) / max_roi) * 0.5
                    + (row["conversions"] / max_conversions) * 0.3
                    + (row["reach"] / max_reach) * 0.2
                )
                * 100,
                1,
            )
            scored_campaigns.append(
                {
                    **row,
                    "campaign_success_score": score,
                }
            )

        best_campaign = max(scored_campaigns, key=lambda item: item["campaign_success_score"]) if scored_campaigns else None
        worst_campaign = min(scored_campaigns, key=lambda item: item["campaign_success_score"]) if scored_campaigns else None

        monthly_revenue: dict[str, float] = defaultdict(float)
        for row in performance:
            monthly_revenue[row["month_period"]] += row["revenue"]

        product_focus_recommendation = (
            f"Scale {best_product[0]} as the hero SKU and remediate {worst_product[0]} with channel-specific pricing or bundling."
            if best_product[0] != "N/A"
            else "No product recommendation is available because sales data is missing."
        )

        unavailable = {
            "CTR": "CTR requires click/impression data, which is not present in the current schema.",
            "CPC": "CPC requires click data, which is not present in the current schema.",
        }

        return {
            "revenue": total_revenue,
            "units_sold": total_units,
            "profit": profit,
            "conversion_rate": conversion_rate,
            "CTR": None,
            "CPC": None,
            "CPA/CAC": cpa,
            "ROAS": roas,
            "ROI": roi,
            "AOV": aov,
            "best_selling_product": {"name": best_product[0], "units_sold": best_product[1]},
            "worst_selling_product": {"name": worst_product[0], "units_sold": worst_product[1]},
            "best_campaign": best_campaign,
            "worst_campaign": worst_campaign,
            "product_focus_recommendation": product_focus_recommendation,
            "campaign_success_score": {
                "average": round(mean([row["campaign_success_score"] for row in scored_campaigns]), 1) if scored_campaigns else 0,
                "top_campaigns": scored_campaigns,
            },
            "total_marketing_spend": total_spend,
            "transactions": transactions,
            "monthly_revenue": dict(monthly_revenue),
            "product_units": dict(sorted(product_units.items(), key=lambda item: item[1], reverse=True)),
            "product_revenue": dict(sorted(product_revenue.items(), key=lambda item: item[1], reverse=True)),
            "campaign_sales": campaign_sales,
            "unavailable_metrics": unavailable,
        }

