# Makefile for AI Marketing Agent System

.PHONY: help build run run-worker run-dev run-prod test clean logs shell

# Default target
help:
	@echo "AI Marketing Agent System - Makefile Commands"
	@echo "=========================================="
	@echo "build       - Build Docker images"
	@echo "run         - Run the FastAPI web service in docker"
	@echo "run-worker  - Run the batch pipeline worker once in docker"
	@echo "run-dev     - Run the web service in development mode"
	@echo "run-prod    - Run the production profile in detached mode"
	@echo "test        - Run backend tests locally"
	@echo "clean       - Clean up docker containers and images"
	@echo "logs        - View web service logs"
	@echo "shell       - Get shell access to the web container"

build:
	docker compose -f infra/docker/docker-compose.yml build

run:
	docker compose -f infra/docker/docker-compose.yml up ai-marketing-web

run-worker:
	docker compose -f infra/docker/docker-compose.yml run --rm --profile batch ai-marketing-worker

run-dev:
	docker compose -f infra/docker/docker-compose.yml -f infra/docker/docker-compose.dev.yml up ai-marketing-web

run-prod:
	docker compose -f infra/docker/docker-compose.yml -f infra/docker/docker-compose.prod.yml up -d ai-marketing-web

test:
	python -m pytest tests -q

clean:
	docker compose -f infra/docker/docker-compose.yml down --remove-orphans --rmi local
	docker image prune -f

logs:
	docker compose -f infra/docker/docker-compose.yml logs -f ai-marketing-web

shell:
	docker exec -it ai-marketing-web /bin/bash
