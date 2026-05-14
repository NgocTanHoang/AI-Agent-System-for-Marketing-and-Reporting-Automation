from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class KPIValue(BaseModel):
    key: str
    label: str
    value: float | int | str | None
    display_value: str
    unit: str | None = None
    status: Literal["ok", "warning", "missing"] = "ok"
    description: str


class ChartConfig(BaseModel):
    chart_type: Literal["bar", "line", "doughnut", "radar", "scatter", "funnel"]
    title: str
    labels: list[str] = Field(default_factory=list)
    datasets: list[dict[str, Any]] = Field(default_factory=list)
    meta: dict[str, Any] = Field(default_factory=dict)


class AgentStatus(BaseModel):
    name: str
    status: Literal["pending", "running", "completed", "failed", "skipped"]
    summary: str = ""
    provider: str | None = None
    model: str | None = None
    latency_ms: int | None = None
    error: str | None = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Recommendation(BaseModel):
    campaign_name: str
    target_audience: str
    product_focus: str
    channel: str
    budget_suggestion: str
    kpi_target: str
    rationale: str
    risk: str


class DashboardData(BaseModel):
    kpi_cards: list[KPIValue]
    charts: dict[str, ChartConfig]
    agent_status: list[AgentStatus]
    insights: list[str]
    recommendations: list[Recommendation]
    last_run: dict[str, Any]


class AgentLogEntry(BaseModel):
    run_id: str
    agent_name: str
    status: str
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class PipelineRunRequest(BaseModel):
    force: bool = False


class PipelineRunResponse(BaseModel):
    run_id: str
    status: Literal["queued", "running", "completed", "failed"]
    message: str


class PipelineState(BaseModel):
    run_id: str | None = None
    status: Literal["IDLE", "RUNNING", "COMPLETED", "FAILED"] = "IDLE"
    started_at: datetime | None = None
    completed_at: datetime | None = None
    report_path: str | None = None
    dashboard_path: str | None = None
    error: str | None = None
    agent_status: list[AgentStatus] = Field(default_factory=list)


class ReportRecord(BaseModel):
    id: str
    filename: str
    title: str
    created_at: datetime
    run_id: str | None = None
    size_kb: float


class ReportPayload(BaseModel):
    id: str
    filename: str
    title: str
    content: str
    created_at: datetime


class ModelProviderStatus(BaseModel):
    provider: str
    model: str
    connected: bool
    mode: Literal["live", "mock"]
    rpm_limit: int | None = None


class HealthPayload(BaseModel):
    status: Literal["ok", "degraded"]
    database_exists: bool
    processed_reports: int
    latest_report: str | None
    pipeline_status: str
    llm_credentials_available: dict[str, bool]
    mock_mode: bool

