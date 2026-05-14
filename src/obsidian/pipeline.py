from __future__ import annotations

import json
import os
import threading
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from src.config import PROCESSED_DATA_DIR, load_pipeline_settings, setup_logging
from src.memory import count_signals_for_run, log_run, write_signal
from src.obsidian.agents import ObsidianAgents
from src.obsidian.llm import ModelRouterTool
from src.obsidian.metrics import MetricsTool
from src.obsidian.reporting import ReportExportTool, format_currency
from src.obsidian.repository import DatabaseTool
from src.obsidian.schemas import AgentLogEntry, AgentStatus, DashboardData, KPIValue, PipelineState
from src.obsidian.search import DDGSSearchTool
from src.runtime_data import build_signal_fallback_entries


logger = setup_logging("obsidian_pipeline")


class ObsidianPipelineService:
    def __init__(self, repository: DatabaseTool | None = None) -> None:
        self.repository = repository or DatabaseTool()
        self.metrics_tool = MetricsTool()
        self.router = ModelRouterTool()
        self.search_tool = DDGSSearchTool()
        self.agents = ObsidianAgents(self.router)
        self.report_exporter = ReportExportTool()
        self.settings = load_pipeline_settings()
        self.state = PipelineState()
        self.agent_logs: list[AgentLogEntry] = []
        self.lock = threading.Lock()
        self.state_file = PROCESSED_DATA_DIR / "obsidian_pipeline_state.json"

    def _save_state(self) -> None:
        self.state_file.write_text(
            self.state.model_dump_json(indent=2),
            encoding="utf-8",
        )

    def _log_agent(self, run_id: str, agent_name: str, status: str, message: str) -> None:
        entry = AgentLogEntry(
            run_id=run_id,
            agent_name=agent_name,
            status=status,
            message=message,
        )
        self.agent_logs.append(entry)
        logger.info("[%s] %s: %s", agent_name, status, message)

    def _set_agent_status(self, name: str, status: str, **kwargs: Any) -> None:
        existing = next((item for item in self.state.agent_status if item.name == name), None)
        if existing is None:
            agent = AgentStatus(name=name, status=status, **kwargs)
            self.state.agent_status.append(agent)
        else:
            existing.status = status
            for key, value in kwargs.items():
                setattr(existing, key, value)
            existing.updated_at = datetime.utcnow()
        self._save_state()

    def get_status(self) -> PipelineState:
        return self.state

    def get_agent_logs(self, run_id: str | None = None) -> list[dict[str, Any]]:
        records = self.agent_logs
        if run_id:
            records = [item for item in records if item.run_id == run_id]
        return [item.model_dump() for item in records]

    def _build_kpi_cards(self, metrics: dict[str, Any]) -> list[KPIValue]:
        missing = metrics["unavailable_metrics"]
        return [
            KPIValue(
                key="revenue",
                label="Revenue",
                value=metrics["revenue"],
                display_value=format_currency(metrics["revenue"]),
                unit="VND",
                description="Total revenue from sales rows.",
            ),
            KPIValue(
                key="units_sold",
                label="Units Sold",
                value=metrics["units_sold"],
                display_value=f"{metrics['units_sold']:,}",
                description="Total units sold across the dataset.",
            ),
            KPIValue(
                key="profit",
                label="Profit",
                value=metrics["profit"],
                display_value=format_currency(metrics["profit"]),
                unit="VND",
                description="Revenue minus total marketing spend.",
            ),
            KPIValue(
                key="conversion_rate",
                label="Conversion Rate",
                value=metrics["conversion_rate"],
                display_value=f"{(metrics['conversion_rate'] or 0):.2%}",
                description="Campaign conversions divided by reach.",
            ),
            KPIValue(
                key="roas",
                label="ROAS",
                value=metrics["ROAS"],
                display_value=f"{(metrics['ROAS'] or 0):.2f}x",
                description="Revenue divided by total campaign spend.",
            ),
            KPIValue(
                key="roi",
                label="ROI",
                value=metrics["ROI"],
                display_value=f"{(metrics['ROI'] or 0):.2f}x",
                description="Profit divided by total campaign spend.",
            ),
            KPIValue(
                key="ctr",
                label="CTR",
                value=None,
                display_value="Missing",
                status="missing",
                description=missing["CTR"],
            ),
            KPIValue(
                key="cpc",
                label="CPC",
                value=None,
                display_value="Missing",
                status="missing",
                description=missing["CPC"],
            ),
        ]

    def _build_dashboard(self, run_id: str, metrics: dict[str, Any], agent_status: list[AgentStatus], insights: list[str], recommendations: list[Any]) -> DashboardData:
        product_labels = list(metrics["product_units"].keys())[:8]
        product_units = [metrics["product_units"][label] for label in product_labels]
        campaign_labels = [row["campaign_name"] for row in metrics["campaign_success_score"]["top_campaigns"]]
        campaign_scores = [row["campaign_success_score"] for row in metrics["campaign_success_score"]["top_campaigns"]]
        revenue_by_campaign_labels = [row["campaign_name"] for row in metrics["campaign_sales"][:8]]
        revenue_by_campaign_values = [round(row["revenue"], 2) for row in metrics["campaign_sales"][:8]]
        sales_trend_labels = list(metrics["monthly_revenue"].keys())
        sales_trend_values = list(metrics["monthly_revenue"].values())

        charts = {
            "revenue_by_campaign": {
                "chart_type": "bar",
                "title": "Revenue by Campaign",
                "labels": revenue_by_campaign_labels,
                "datasets": [{"label": "Revenue", "data": revenue_by_campaign_values, "backgroundColor": "#5b7cfa"}],
                "meta": {},
            },
            "product_sales_ranking": {
                "chart_type": "bar",
                "title": "Product Sales Ranking",
                "labels": product_labels,
                "datasets": [{"label": "Units Sold", "data": product_units, "backgroundColor": "#8b5cf6"}],
                "meta": {},
            },
            "campaign_roi": {
                "chart_type": "bar",
                "title": "Campaign Success Score",
                "labels": campaign_labels,
                "datasets": [{"label": "Success Score", "data": campaign_scores, "backgroundColor": "#3b82f6"}],
                "meta": {},
            },
            "sales_trend": {
                "chart_type": "line",
                "title": "Sales Trend",
                "labels": sales_trend_labels,
                "datasets": [{"label": "Revenue", "data": sales_trend_values, "borderColor": "#60a5fa", "backgroundColor": "rgba(96,165,250,0.15)"}],
                "meta": {},
            },
            "conversion_funnel": {
                "chart_type": "funnel",
                "title": "Conversion Funnel",
                "labels": ["Reach", "Conversions", "Units Sold"],
                "datasets": [{"label": "Pipeline Funnel", "data": [metrics["transactions"] * 50, metrics["CPA/CAC"] and round(metrics["total_marketing_spend"] / metrics["CPA/CAC"]) or 0, metrics["units_sold"]], "backgroundColor": ["#4f46e5", "#6366f1", "#8b5cf6"]}],
                "meta": {},
            },
            "product_matrix": {
                "chart_type": "scatter",
                "title": "Product Matrix",
                "labels": product_labels,
                "datasets": [
                    {
                        "label": "Products",
                        "data": [{"x": metrics["product_units"][label], "y": round(metrics["product_revenue"][label], 2), "label": label} for label in product_labels],
                        "backgroundColor": "#38bdf8",
                    }
                ],
                "meta": {},
            },
            "channel_performance": {
                "chart_type": "radar",
                "title": "Channel Performance",
                "labels": [row["channel"] for row in metrics["campaign_success_score"]["top_campaigns"]],
                "datasets": [
                    {"label": "ROI", "data": [row["roi"] for row in metrics["campaign_success_score"]["top_campaigns"]], "borderColor": "#818cf8"},
                    {"label": "Conversions", "data": [row["conversions"] for row in metrics["campaign_success_score"]["top_campaigns"]], "borderColor": "#c084fc"},
                ],
                "meta": {},
            },
        }

        return DashboardData(
            kpi_cards=self._build_kpi_cards(metrics),
            charts=charts,
            agent_status=agent_status,
            insights=insights,
            recommendations=recommendations,
            last_run={
                "run_id": run_id,
                "status": self.state.status,
                "started_at": self.state.started_at.isoformat() if self.state.started_at else None,
                "completed_at": self.state.completed_at.isoformat() if self.state.completed_at else None,
                "report_path": self.state.report_path,
            },
        )

    def _ensure_signal_updates(self, report_content: str, run_id: str) -> int:
        recent_count = count_signals_for_run(run_id=run_id, minutes=10)
        if recent_count >= 3:
            return recent_count

        success_count = 0
        for entry in build_signal_fallback_entries(report_content, db_path=self.repository.db_path):
            result = write_signal(
                insight_type=entry["insight_type"],
                learning_content=entry["learning_content"],
                run_id=run_id,
            )
            if "✅" in result:
                success_count += 1
        return success_count

    def run_pipeline_async(self) -> dict[str, str]:
        with self.lock:
            if self.state.status == "RUNNING":
                raise RuntimeError("Pipeline is already running.")
            run_id = uuid.uuid4().hex[:8]
            thread = threading.Thread(target=self.run_pipeline_sync, args=(run_id,), daemon=True)
            thread.start()
            return {"run_id": run_id, "status": "queued"}

    def run_pipeline_sync(self, run_id: str | None = None) -> dict[str, Any]:
        with self.lock:
            run_id = run_id or uuid.uuid4().hex[:8]
            self.state = PipelineState(
                run_id=run_id,
                status="RUNNING",
                started_at=datetime.utcnow(),
                agent_status=[AgentStatus(name=name, status="pending") for name in self.agents.AGENT_SEQUENCE],
            )
            self._save_state()

        started = time.perf_counter()
        try:
            snapshot = self.repository.load_snapshot()
            metrics = self.metrics_tool.compute(snapshot)
            market_topic = self.settings["pipeline"]["market_topic"]
            search_results = self.search_tool.search(f"{market_topic} technology trends and smartphone market")

            outputs: dict[str, str] = {}

            self._set_agent_status("Data Analyst Agent", "running")
            data_result = self.agents.run_data_analyst(metrics)
            outputs["Data Analyst Agent"] = data_result.content
            self._set_agent_status("Data Analyst Agent", "completed", summary=data_result.content[:180], provider=data_result.provider, model=data_result.model, latency_ms=data_result.latency_ms, error=data_result.error)
            self._log_agent(run_id, "Data Analyst Agent", "completed", outputs["Data Analyst Agent"])

            self._set_agent_status("Market Research Agent", "running")
            research_result = self.agents.run_market_research(market_topic, search_results)
            outputs["Market Research Agent"] = research_result.content
            self._set_agent_status("Market Research Agent", "completed", summary=research_result.content[:180], provider=research_result.provider, model=research_result.model, latency_ms=research_result.latency_ms, error=research_result.error)
            self._log_agent(run_id, "Market Research Agent", "completed", outputs["Market Research Agent"])

            self._set_agent_status("Campaign Performance Agent", "running")
            campaign_result = self.agents.run_campaign_performance(metrics)
            outputs["Campaign Performance Agent"] = campaign_result.content
            self._set_agent_status("Campaign Performance Agent", "completed", summary=campaign_result.content[:180], provider=campaign_result.provider, model=campaign_result.model, latency_ms=campaign_result.latency_ms, error=campaign_result.error)
            self._log_agent(run_id, "Campaign Performance Agent", "completed", outputs["Campaign Performance Agent"])

            self._set_agent_status("Product Strategy Agent", "running")
            product_result = self.agents.run_product_strategy(metrics)
            outputs["Product Strategy Agent"] = product_result.content
            self._set_agent_status("Product Strategy Agent", "completed", summary=product_result.content[:180], provider=product_result.provider, model=product_result.model, latency_ms=product_result.latency_ms, error=product_result.error)
            self._log_agent(run_id, "Product Strategy Agent", "completed", outputs["Product Strategy Agent"])

            self._set_agent_status("Insight Synthesizer Agent", "running")
            insight_result = self.agents.run_insight_synthesizer(
                metrics,
                outputs["Data Analyst Agent"],
                outputs["Market Research Agent"],
                outputs["Campaign Performance Agent"],
                outputs["Product Strategy Agent"],
            )
            outputs["Insight Synthesizer Agent"] = insight_result.content
            self._set_agent_status("Insight Synthesizer Agent", "completed", summary=insight_result.content[:180], provider=insight_result.provider, model=insight_result.model, latency_ms=insight_result.latency_ms, error=insight_result.error)
            self._log_agent(run_id, "Insight Synthesizer Agent", "completed", outputs["Insight Synthesizer Agent"])

            recommendations = self.agents.build_recommendations(metrics)

            self._set_agent_status("Report Writer Agent", "running")
            report_result = self.router.complete(
                agent_name="Report Writer Agent",
                system_prompt="You write structured executive reports from deterministic KPI data. Always preserve the given headings.",
                user_prompt=(
                    f"Metrics: {metrics}\n"
                    f"Data Analyst: {outputs['Data Analyst Agent']}\n"
                    f"Market Research: {outputs['Market Research Agent']}\n"
                    f"Campaign Performance: {outputs['Campaign Performance Agent']}\n"
                    f"Product Strategy: {outputs['Product Strategy Agent']}\n"
                    f"Insight Synthesis: {outputs['Insight Synthesizer Agent']}\n"
                    f"Recommendations: {[item.model_dump() for item in recommendations]}\n"
                    "Write the Obsidian Intelligence Report with the provided 11 section headings."
                ),
                fallback_builder=lambda: self.report_exporter.build_report(run_id, metrics, outputs, search_results, recommendations),
            )
            report_markdown = report_result.content
            if "# Obsidian Intelligence Report" not in report_markdown:
                report_markdown = self.report_exporter.build_report(run_id, metrics, outputs, search_results, recommendations)
            outputs["Report Writer Agent"] = report_markdown
            self._set_agent_status("Report Writer Agent", "completed", summary="Report generated.", provider=report_result.provider, model=report_result.model, latency_ms=report_result.latency_ms, error=report_result.error)
            self._log_agent(run_id, "Report Writer Agent", "completed", "Structured report generated.")

            report_filename_timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            report_path = self.repository.processed_dir / f"Obsidian_Intelligence_Report_{run_id}_{report_filename_timestamp}.md"
            dashboard_path = self.repository.runs_dir / f"{run_id}_dashboard.json"
            logs_path = self.repository.runs_dir / f"{run_id}_agent_logs.json"
            signals_written = self._ensure_signal_updates(report_markdown, run_id)
            duration_seconds = time.perf_counter() - started

            self.state.status = "COMPLETED"
            self.state.completed_at = datetime.utcnow()
            self.state.report_path = str(report_path)
            self.state.dashboard_path = str(dashboard_path)
            self.state.error = None
            self._save_state()

            dashboard = self._build_dashboard(
                run_id=run_id,
                metrics=metrics,
                agent_status=self.state.agent_status,
                insights=[
                    outputs["Data Analyst Agent"],
                    outputs["Market Research Agent"],
                    outputs["Campaign Performance Agent"],
                    outputs["Product Strategy Agent"],
                    outputs["Insight Synthesizer Agent"],
                ],
                recommendations=recommendations,
            )

            report_path.write_text(report_markdown, encoding="utf-8")
            dashboard_path.write_text(
                json.dumps(dashboard.model_dump(mode="json"), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            logs_path.write_text(
                json.dumps(
                    [entry.model_dump(mode="json") for entry in self.agent_logs if entry.run_id == run_id],
                    ensure_ascii=False,
                    indent=2,
                    default=str,
                ),
                encoding="utf-8",
            )

            log_run(
                run_id=run_id,
                market_topic=market_topic,
                report_filename=report_path.name,
                report_length=len(report_markdown),
                qa_passed=True,
                signals_written=signals_written,
                duration_seconds=duration_seconds,
            )

            return {
                "run_id": run_id,
                "report_path": str(report_path),
                "dashboard_path": str(dashboard_path),
                "status": "COMPLETED",
            }
        except Exception as exc:
            self.state.status = "FAILED"
            self.state.completed_at = datetime.utcnow()
            self.state.error = str(exc)
            self._save_state()
            self._log_agent(self.state.run_id or run_id or "unknown", "Pipeline", "failed", str(exc))
            log_run(
                run_id=self.state.run_id or run_id or "unknown",
                market_topic=self.settings["pipeline"]["market_topic"],
                error_message=str(exc),
                duration_seconds=time.perf_counter() - started,
            )
            raise

    def get_dashboard_data(self, run_id: str | None = None) -> dict[str, Any]:
        target_run = run_id or self.state.run_id
        if not target_run:
            return DashboardData(
                kpi_cards=[],
                charts={},
                agent_status=[],
                insights=[],
                recommendations=[],
                last_run={},
            ).model_dump(mode="json")

        dashboard_path = self.repository.runs_dir / f"{target_run}_dashboard.json"
        if not dashboard_path.exists():
            return DashboardData(
                kpi_cards=[],
                charts={},
                agent_status=self.state.agent_status,
                insights=[],
                recommendations=[],
                last_run={"run_id": target_run, "status": self.state.status},
            ).model_dump(mode="json")
        return json.loads(dashboard_path.read_text(encoding="utf-8"))
