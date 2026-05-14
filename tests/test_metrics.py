from src.obsidian.metrics import MetricsTool


def test_metrics_tool_computes_deterministic_values():
    snapshot = {
        "sales": [
            {"model_name": "Alpha", "units_sold": 10, "unit_price": 100, "campaign_id": 1},
            {"model_name": "Beta", "units_sold": 4, "unit_price": 200, "campaign_id": 2},
        ],
        "campaigns": [
            {"campaign_name": "A", "channel": "TikTok", "budget": 500, "reach": 1000, "conversions": 50, "roi": 2.0},
            {"campaign_name": "B", "channel": "Meta", "budget": 250, "reach": 600, "conversions": 15, "roi": 0.8},
        ],
        "campaign_sales": [
            {"campaign_name": "A", "channel": "TikTok", "revenue": 1000, "units_sold": 10},
            {"campaign_name": "B", "channel": "Meta", "revenue": 800, "units_sold": 4},
        ],
        "performance": [{"month_period": "2026-03", "model_name": "Alpha", "units_sold": 10, "revenue": 1000}],
    }

    metrics = MetricsTool().compute(snapshot)

    assert metrics["revenue"] == 1800
    assert metrics["units_sold"] == 14
    assert metrics["profit"] == 1050
    assert round(metrics["ROAS"], 2) == 2.4
    assert metrics["best_selling_product"]["name"] == "Alpha"
    assert metrics["worst_selling_product"]["name"] == "Beta"
    assert metrics["CTR"] is None
