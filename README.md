# AI Agent System for Marketing and Reporting Automation

Multi-agent marketing intelligence system gồm:

- FastAPI backend cho dashboard và API
- CrewAI pipeline để research, planning và report generation
- React/Vite frontend cho analytics và pipeline monitoring
- SQLite + ChromaDB cho dữ liệu nghiệp vụ, report history và memory signals

## Kiến trúc nhanh

- `app.py`: FastAPI app và dashboard/API endpoints
- `main.py`: pipeline batch runner
- `src/agents.py`, `src/tasks.py`, `src/tools.py`: agent orchestration
- `src/memory.py`: long-term learning signals
- `frontend/`: React dashboard
- `infra/docker/`: Dockerfiles và compose
- `tests/`: backend/API/pipeline tests

## Yêu cầu

- Python 3.11+
- Node.js 20+
- Docker Desktop nếu muốn chạy bằng container
- Ít nhất một API key để chạy pipeline LLM thật:
  - `NVIDIA_NIM_API_KEY` hoặc `NVIDIA_API_KEY`
  - `OPENROUTER_API_KEY`

## Cấu hình môi trường

Tạo `.env` từ `.env.example`:

```bash
cp .env.example .env
```

Các biến chính:

```env
NVIDIA_NIM_API_KEY=
NVIDIA_API_KEY=
OPENROUTER_API_KEY=
VITE_API_BASE_URL=
```

`VITE_API_BASE_URL` có thể để trống để frontend dùng relative path.

## Chạy local backend

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt -r requirements-dev.txt
python src/init_db.py
python -m uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

Các endpoint quan trọng:

- `GET /api/health`
- `GET /api/pipeline-status`
- `GET /api/pipeline-logs`
- `POST /run`
- `GET /api/kpi-summary`
- `GET /api/dashboard-data`
- `GET /api/reports`
- `GET /api/report/{filename}`
- `POST /api/rate-report`
- `GET /api/model-info`
- `GET /api/social-posts`

## Chạy local frontend

```bash
cd frontend
npm ci
npm run dev
```

Mặc định Vite proxy các route `/api` và `/run` sang `http://localhost:8000`.

Nếu frontend deploy riêng domain/host khác backend, set:

```env
VITE_API_BASE_URL=https://your-api-host
```

## Chạy pipeline batch

Pipeline thật cần API key LLM hợp lệ:

```bash
python main.py
```

Output sẽ được ghi vào `data/processed/`.

## Chạy full Docker Compose

Web/API:

```bash
docker compose -f infra/docker/docker-compose.yml up --build ai-marketing-web
```

Batch worker one-off:

```bash
docker compose -f infra/docker/docker-compose.yml run --rm --profile batch ai-marketing-worker
```

Hoặc qua Makefile:

```bash
make build
make run
make run-worker
```

## Test và kiểm tra

```bash
python -m compileall app.py main.py src tests
python -m pytest tests -q
```

Frontend build:

```bash
cd frontend
npm ci
npm run build
```

Health check local/container:

```bash
python infra/healthcheck.py --mode worker
python infra/healthcheck.py --mode web --url http://127.0.0.1:8000/api/health
```

## CI/CD

Workflow GitHub Actions hiện chạy:

- Python dependency install
- `compileall`
- backend tests
- frontend build
- Docker smoke build cho web và worker
- push image web/worker khi push vào `main`

## Report output kỳ vọng

Pipeline được thiết kế để sinh report chiến lược có cấu trúc rõ ràng. Prompt/report review hiện nhắm tới các khối nội dung sau:

1. Executive Summary
2. Campaign Objective
3. Target Audience
4. Market & Competitor Insights
5. Key Findings
6. Strategic Recommendations
7. Content Plan
8. Channel Strategy
9. KPI & Measurement Plan
10. Risks & Mitigations
11. Next Actions

## Lưu ý thực tế

- Dashboard/API và test có thể chạy mà không cần API key.
- Pipeline LLM thật không thể xác minh end-to-end nếu thiếu secret hợp lệ.
- ChromaDB data trong `data/chromadb/` là runtime state; cần quản lý riêng nếu deploy production.
