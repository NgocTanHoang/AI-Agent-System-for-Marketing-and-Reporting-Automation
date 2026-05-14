# Obsidian Intelligence System - AI Marketing Agent Dashboard V2.0

Obsidian Intelligence System là bản refactor của hệ thống marketing intelligence theo hướng backend-first:

- FastAPI backend với contract API rõ ràng
- Multi-agent pipeline có `run_id`, trạng thái, agent logs, dashboard artifacts và report artifacts
- KPI marketing được tính deterministic bằng Python, không giao cho LLM
- Model router: NVIDIA primary, OpenRouter fallback, có mock mode và throttle cho NVIDIA
- React/Vite frontend với dashboard dark cyber-enterprise và Chart.js

## Kiến trúc

- [app.py](C:/Users/Ngoc%20Tan/.codex/worktrees/a9ea/01_AI%20Agent%20System%20for%20Marketing%20and%20Reporting%20Automation/app.py): FastAPI app
- [main.py](C:/Users/Ngoc%20Tan/.codex/worktrees/a9ea/01_AI%20Agent%20System%20for%20Marketing%20and%20Reporting%20Automation/main.py): CLI batch runner
- [src/obsidian/schemas.py](C:/Users/Ngoc%20Tan/.codex/worktrees/a9ea/01_AI%20Agent%20System%20for%20Marketing%20and%20Reporting%20Automation/src/obsidian/schemas.py): Pydantic contracts
- [src/obsidian/repository.py](C:/Users/Ngoc%20Tan/.codex/worktrees/a9ea/01_AI%20Agent%20System%20for%20Marketing%20and%20Reporting%20Automation/src/obsidian/repository.py): database/report persistence
- [src/obsidian/metrics.py](C:/Users/Ngoc%20Tan/.codex/worktrees/a9ea/01_AI%20Agent%20System%20for%20Marketing%20and%20Reporting%20Automation/src/obsidian/metrics.py): deterministic KPI engine
- [src/obsidian/llm.py](C:/Users/Ngoc%20Tan/.codex/worktrees/a9ea/01_AI%20Agent%20System%20for%20Marketing%20and%20Reporting%20Automation/src/obsidian/llm.py): model router và throttle
- [src/obsidian/search.py](C:/Users/Ngoc%20Tan/.codex/worktrees/a9ea/01_AI%20Agent%20System%20for%20Marketing%20and%20Reporting%20Automation/src/obsidian/search.py): DDGS search wrapper
- [src/obsidian/agents.py](C:/Users/Ngoc%20Tan/.codex/worktrees/a9ea/01_AI%20Agent%20System%20for%20Marketing%20and%20Reporting%20Automation/src/obsidian/agents.py): agent orchestration
- [src/obsidian/pipeline.py](C:/Users/Ngoc%20Tan/.codex/worktrees/a9ea/01_AI%20Agent%20System%20for%20Marketing%20and%20Reporting%20Automation/src/obsidian/pipeline.py): pipeline service, state, artifacts
- [frontend/src](C:/Users/Ngoc%20Tan/.codex/worktrees/a9ea/01_AI%20Agent%20System%20for%20Marketing%20and%20Reporting%20Automation/frontend/src): dashboard V2

## API bắt buộc

- `POST /api/run-pipeline`
- `GET /api/pipeline-status`
- `GET /api/agent-logs`
- `GET /api/dashboard-data`
- `GET /api/reports`
- `GET /api/report/{id}`
- `GET /api/model-info`
- `GET /api/health`

## Biến môi trường

Tạo `.env` từ `.env.example`.

Biến chính:

```env
NVIDIA_NIM_API_KEY=
NVIDIA_API_KEY=
OPENROUTER_API_KEY=
MODEL_PROVIDER=auto
ENABLE_MOCK_LLM=true
DDGS_ENABLED=true
NVIDIA_RPM_LIMIT=40
OPENROUTER_MODEL_ID=openai/gpt-oss-120b:free
OPENROUTER_MODEL_NAME=gpt-oss-120b (free)
OPENROUTER_MODEL_CONTEXT_WINDOW=131K
VITE_API_BASE_URL=
```

## Chạy local backend

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt -r requirements-dev.txt
python src/init_db.py
python -m uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

## Chạy local frontend

```bash
cd frontend
npm ci
npm run dev
```

`VITE_API_BASE_URL` có thể để trống để frontend dùng same-host relative path hoặc Vite proxy.

## Chạy pipeline batch

Mock mode:

```bash
set ENABLE_MOCK_LLM=true
set DDGS_ENABLED=false
python main.py
```

Live mode:

```bash
set ENABLE_MOCK_LLM=false
set DDGS_ENABLED=true
python main.py
```

## Docker

```bash
docker build -f infra/docker/Dockerfile .
docker build -f infra/docker/Dockerfile.worker .
docker compose -f infra/docker/docker-compose.yml up --build ai-marketing-web
```

## Test

```bash
python -m compileall app.py main.py src tests
python -m pytest tests -q
cd frontend
npm run build
```

## Report output

Report chuẩn mới:

1. Executive Summary
2. Data Sources
3. Campaign Performance Overview
4. Product Performance Analysis
5. Market & Technology Signals
6. Key Charts Interpretation
7. Strategic Insights
8. Recommended Campaigns
9. Product Focus Plan
10. Risks & Limitations
11. Next Actions
