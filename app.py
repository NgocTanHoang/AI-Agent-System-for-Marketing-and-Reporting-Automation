from __future__ import annotations

import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.config import DATABASE_PATH, PROCESSED_DATA_DIR, get_runtime_model_info, load_pipeline_settings
from src.init_db import init_db
from src.obsidian.pipeline import ObsidianPipelineService
from src.obsidian.repository import DatabaseTool
from src.obsidian.schemas import HealthPayload, PipelineRunRequest, PipelineRunResponse


SETTINGS = load_pipeline_settings()
REPOSITORY = DatabaseTool()
PIPELINE = ObsidianPipelineService(repository=REPOSITORY)


def _ensure_database_ready() -> None:
    if not DATABASE_PATH.exists():
        init_db(str(DATABASE_PATH))


_ensure_database_ready()

app = FastAPI(title="Obsidian Intelligence System - AI Marketing Agent Dashboard V2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root() -> dict[str, str]:
    return {
        "name": "Obsidian Intelligence System",
        "status": "online",
        "docs_hint": "Use the /api/* endpoints from the dashboard.",
    }


@app.get("/api/health")
async def get_health() -> JSONResponse:
    runtime = get_runtime_model_info(settings=SETTINGS)
    payload = HealthPayload(
        status="ok" if DATABASE_PATH.exists() else "degraded",
        database_exists=DATABASE_PATH.exists(),
        processed_reports=len(list(PROCESSED_DATA_DIR.glob("Obsidian_Intelligence_Report_*.md"))),
        latest_report=REPOSITORY.latest_report_name(),
        pipeline_status=PIPELINE.get_status().status,
        llm_credentials_available={
            "primary": runtime["primary_model"]["api_connected"],
            "backup": runtime["backup_provider"]["api_connected"],
        },
        mock_mode=os.getenv("ENABLE_MOCK_LLM", "false").lower() in {"1", "true", "yes", "on"},
    )
    return JSONResponse(
        status_code=200 if payload.status == "ok" else 503,
        content=payload.model_dump(mode="json"),
    )


@app.post("/api/run-pipeline")
async def run_pipeline(request: PipelineRunRequest) -> JSONResponse:
    state = PIPELINE.get_status()
    if state.status == "RUNNING" and not request.force:
        raise HTTPException(status_code=409, detail="Pipeline is already running.")

    response = PIPELINE.run_pipeline_async()
    payload = PipelineRunResponse(
        run_id=response["run_id"],
        status=response["status"],
        message="Pipeline queued successfully.",
    )
    return JSONResponse(status_code=202, content=payload.model_dump(mode="json"))


@app.post("/run")
async def legacy_run_pipeline() -> JSONResponse:
    return await run_pipeline(PipelineRunRequest())


@app.get("/api/pipeline-status")
async def pipeline_status() -> dict:
    return PIPELINE.get_status().model_dump(mode="json")


@app.get("/api/agent-logs")
async def agent_logs(run_id: str | None = None) -> dict[str, list[dict]]:
    return {"logs": PIPELINE.get_agent_logs(run_id=run_id)}


@app.get("/api/dashboard-data")
async def dashboard_data(run_id: str | None = None) -> dict:
    return PIPELINE.get_dashboard_data(run_id=run_id)


@app.get("/api/reports")
async def list_reports() -> dict[str, list[dict]]:
    return {"reports": REPOSITORY.list_reports()}


@app.get("/api/report/{report_id}")
async def get_report(report_id: str) -> dict:
    report = REPOSITORY.get_report(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found.")
    return report


@app.get("/api/model-info")
async def get_model_info() -> dict:
    runtime = get_runtime_model_info(settings=SETTINGS)
    runtime["router"] = {
        "selected_mode": os.getenv("MODEL_PROVIDER", "auto"),
        "mock_mode": os.getenv("ENABLE_MOCK_LLM", "false").lower() in {"1", "true", "yes", "on"},
        "nvidia_rpm_limit": int(os.getenv("NVIDIA_RPM_LIMIT", "40")),
    }
    return runtime


@app.get("/api/pipeline-logs")
async def legacy_pipeline_logs(run_id: str | None = None) -> dict[str, list[dict]]:
    return {"logs": PIPELINE.get_agent_logs(run_id=run_id)}


@app.get("/api/social-posts")
async def legacy_social_posts() -> dict:
    dashboard = PIPELINE.get_dashboard_data()
    return {"posts": dashboard.get("insights", [])}


@app.get("/api/kpi-summary")
async def legacy_kpi_summary() -> dict:
    dashboard = PIPELINE.get_dashboard_data()
    return {"kpi_cards": dashboard.get("kpi_cards", [])}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
