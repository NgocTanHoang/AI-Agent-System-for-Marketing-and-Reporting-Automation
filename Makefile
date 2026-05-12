# Makefile for AI Marketing Agent System

.PHONY: help build run test clean logs shell

# Default target
help:
	@echo "AI Marketing Agent System - Makefile Commands"
	@echo "=========================================="
	@echo "build      - Build Docker images"
	@echo "run        - Run the application in docker"
	@echo "run-dev    - Run the application in development mode"
	@echo "run-prod   - Run the application in production mode"
	@echo "test       - Run tests"
	@echo "clean      - Clean up docker containers and images"
	@echo "logs       - View application logs"
	@echo "shell      - Get shell access to the container"

# Build the Docker images
build:
	docker-compose -f infra/docker/docker-compose.yml build

# Run the application
run:
	docker-compose -f infra/docker/docker-compose.yml up ai-marketing-agent

# Run the application in development mode
run-dev:
	docker-compose -f infra/docker/docker-compose.yml -f infra/docker/docker-compose.dev.yml up

# Run the application in production mode
run-prod:
	docker-compose -f infra/docker/docker-compose.yml -f infra/docker/docker-compose.prod.yml up -d

# Run tests
test:
	docker run --rm ai-marketing-agent python -m pytest tests/

# Clean up docker containers and images
clean:
	docker-compose -f infra/docker/docker-compose.yml down --rmi all
	docker image prune -f

# View application logs
logs:
	docker-compose -f infra/docker/docker-compose.yml logs -f ai-marketing-agent

# Get shell access to the container
shell:
	docker exec -it ai-marketing-agent /bin/bash