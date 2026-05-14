from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from src.config import DATABASE_PATH, PROCESSED_DATA_DIR


class DatabaseTool:
    REQUIRED_TABLES = {
        "sales",
        "marketing_campaigns",
        "social_sentiment",
        "sales_performance",
        "competitor_products",
    }

    def __init__(self, db_path: str | Path | None = None, processed_dir: str | Path | None = None) -> None:
        self.db_path = Path(db_path or DATABASE_PATH)
        self.processed_dir = Path(processed_dir or PROCESSED_DATA_DIR)
        self.runs_dir = self.processed_dir / "obsidian_runs"
        self.runs_dir.mkdir(parents=True, exist_ok=True)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def database_exists(self) -> bool:
        return self.db_path.exists()

    def validate_schema(self) -> list[str]:
        if not self.database_exists():
            return ["Database file is missing."]

        with self._connect() as conn:
            rows = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        existing = {row["name"] for row in rows}
        missing = sorted(self.REQUIRED_TABLES - existing)
        return [f"Missing required table: {name}" for name in missing]

    def fetch_rows(self, query: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
        with self._connect() as conn:
            return [dict(row) for row in conn.execute(query, params).fetchall()]

    def fetch_one(self, query: str, params: tuple[Any, ...] = ()) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute(query, params).fetchone()
        return dict(row) if row else None

    def load_snapshot(self) -> dict[str, Any]:
        schema_errors = self.validate_schema()
        if schema_errors:
            raise ValueError("; ".join(schema_errors))

        sales = self.fetch_rows("SELECT * FROM sales")
        campaigns = self.fetch_rows("SELECT * FROM marketing_campaigns")
        sentiments = self.fetch_rows(
            """
            SELECT keyword, positive_score, negative_score, total_mentions, top_complaint,
                   trending_platform, top_emotion
            FROM social_sentiment
            ORDER BY total_mentions DESC
            """
        )
        performance = self.fetch_rows(
            "SELECT month_period, model_name, units_sold, revenue FROM sales_performance ORDER BY month_period ASC"
        )
        competitors = self.fetch_rows(
            "SELECT brand, model_name, current_price, strengths, weaknesses FROM competitor_products"
        )
        campaign_sales = self.fetch_rows(
            """
            SELECT COALESCE(mc.campaign_name, 'Organic / Unattributed') AS campaign_name,
                   COALESCE(mc.channel, 'Unknown') AS channel,
                   SUM(s.units_sold * s.unit_price) AS revenue,
                   SUM(s.units_sold) AS units_sold
            FROM sales s
            LEFT JOIN marketing_campaigns mc ON mc.id = s.campaign_id
            GROUP BY COALESCE(mc.campaign_name, 'Organic / Unattributed'), COALESCE(mc.channel, 'Unknown')
            ORDER BY revenue DESC
            """
        )

        return {
            "sales": sales,
            "campaigns": campaigns,
            "sentiments": sentiments,
            "performance": performance,
            "competitors": competitors,
            "campaign_sales": campaign_sales,
            "snapshot_time": datetime.utcnow().isoformat(),
        }

    def save_run_artifacts(
        self,
        run_id: str,
        dashboard_data: dict[str, Any],
        report_markdown: str,
        agent_logs: list[dict[str, Any]],
    ) -> dict[str, str]:
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        report_path = self.processed_dir / f"Obsidian_Intelligence_Report_{run_id}_{timestamp}.md"
        dashboard_path = self.runs_dir / f"{run_id}_dashboard.json"
        logs_path = self.runs_dir / f"{run_id}_agent_logs.json"

        report_path.write_text(report_markdown, encoding="utf-8")
        dashboard_path.write_text(json.dumps(dashboard_data, ensure_ascii=False, indent=2), encoding="utf-8")
        logs_path.write_text(json.dumps(agent_logs, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

        return {
            "report_path": str(report_path),
            "dashboard_path": str(dashboard_path),
            "logs_path": str(logs_path),
        }

    def list_reports(self) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        for path in sorted(self.processed_dir.glob("Obsidian_Intelligence_Report_*.md"), key=lambda item: item.stat().st_mtime, reverse=True):
            stem = path.stem.replace("Obsidian_Intelligence_Report_", "")
            parts = stem.split("_")
            run_id = parts[0] if parts else None
            records.append(
                {
                    "id": stem,
                    "filename": path.name,
                    "title": "Obsidian Intelligence Report",
                    "created_at": datetime.fromtimestamp(path.stat().st_mtime),
                    "size_kb": round(path.stat().st_size / 1024.0, 2),
                    "run_id": run_id,
                }
            )
        return records

    def get_report(self, report_id: str) -> dict[str, Any] | None:
        for record in self.list_reports():
            if record["id"] == report_id or record["filename"] == report_id:
                path = self.processed_dir / record["filename"]
                return {
                    **record,
                    "content": path.read_text(encoding="utf-8"),
                }
        return None

    def latest_report_name(self) -> str | None:
        reports = self.list_reports()
        return reports[0]["filename"] if reports else None
