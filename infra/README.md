# Infrastructure Notes

## Docker assets

- `infra/docker/Dockerfile`: web/API image, chạy FastAPI bằng Uvicorn
- `infra/docker/Dockerfile.worker`: batch pipeline image, chạy `main.py`
- `infra/docker/docker-compose.yml`: compose gốc cho web và worker
- `infra/docker/docker-compose.dev.yml`: mount source code để dev
- `infra/docker/docker-compose.prod.yml`: override production profile
- `infra/healthcheck.py`: health check cho web/worker mode

## Compose services

- `ai-marketing-web`: FastAPI dashboard và API trên cổng `8000`
- `ai-marketing-worker`: service batch one-off, bật qua profile `batch`

## Commands

```bash
docker compose -f infra/docker/docker-compose.yml up --build ai-marketing-web
docker compose -f infra/docker/docker-compose.yml run --rm --profile batch ai-marketing-worker
python infra/healthcheck.py --mode web --url http://127.0.0.1:8000/api/health
python infra/healthcheck.py --mode worker
```
