FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements-web.txt ./

RUN pip install --upgrade pip && \
    pip install -r requirements-web.txt

COPY app.py ./
COPY src ./src
COPY templates ./templates
COPY config ./config
COPY infra/healthcheck.py ./infra/healthcheck.py

RUN useradd --create-home --shell /bin/bash app && \
    mkdir -p data/raw/marketing_content data/processed logs && \
    chown -R app:app /app

USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
  CMD ["python", "infra/healthcheck.py", "--mode", "web"]

CMD ["python", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
