# AI Marketing Agent System - Infrastructure

## Docker Setup

This directory contains Docker configuration files for running the AI Marketing Agent System in containers.

## Docker Files

- `infra/docker/Dockerfile` - Main Docker image definition
- `infra/docker/docker-compose.yml` - Base docker-compose configuration
- `infra/docker/docker-compose.dev.yml` - Development override
- `infra/docker/docker-compose.prod.yml` - Production override
- `infra/docker/.dockerignore` - Files to exclude from Docker build context

## Quick Start

### Prerequisites

1. Docker and Docker Compose installed
2. API keys for LLM providers in `.env` file

### Running the Application

```bash
# Build and run in development mode
make run-dev

# Or with docker-compose directly
docker-compose -f infra/docker/docker-compose.yml -f infra/docker/docker-compose.dev.yml up
```

### Environment Variables

Make sure your `.env` file contains the necessary API keys:

```
NVIDIA_NIM_API_KEY=your_nvidia_api_key
OPENROUTER_API_KEY=your_openrouter_api_key
```

## Docker Configuration Details

### Base Dockerfile

The base Dockerfile uses Python 3.11-slim as the base image and includes:

- System dependencies installation
- Python dependencies installation
- Non-root user for security
- Proper volume mounting for data persistence
- Exposed port for web interface (if applicable)

### Docker Compose Services

1. `ai-marketing-agent` - Main service running the AI agent
2. `ai-marketing-web` (optional) - Web interface service

### Volume Mounts

- `./data:/app/data` - Persist data between container restarts
- `./logs:/app/logs` - Persist logs for monitoring

### Environment Configuration

The system supports different environments:

- Development: Uses live code mounting for rapid development
- Production: Optimized for performance and stability
- Testing: Isolated environment for running tests

## Makefile Commands

- `make build` - Build Docker images (uses infra/docker/docker-compose.yml)
- `make run` - Run the application (uses infra/docker/docker-compose.yml)
- `make run-dev` - Run in development mode (uses infra/docker/docker-compose.yml and infra/docker/docker-compose.dev.yml)
- `make run-prod` - Run in production mode (uses infra/docker/docker-compose.yml and infra/docker/docker-compose.prod.yml)
- `make test` - Run tests
- `make clean` - Clean up containers and images (uses infra/docker/docker-compose.yml)
- `make logs` - View application logs (uses infra/docker/docker-compose.yml)
- `make shell` - Get shell access to container