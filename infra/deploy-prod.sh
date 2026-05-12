#!/bin/bash

#!/bin/bash

# Production deployment script for AI Marketing Agent System

# Exit on any error
set -e

echo "Starting production deployment of AI Marketing Agent System..."

# Check if running as root (optional security check)
if [ "$EUID" -eq 0 ]; then
    echo "Warning: Running as root. Consider using a non-root user for production."
fi

# Create necessary directories
mkdir -p data/raw/marketing_content data/processed logs

# Pull the latest images
echo "Pulling latest Docker images..."
docker-compose -f infra/docker/docker-compose.yml -f infra/docker/docker-compose.prod.yml pull

# Build images if they don't exist
echo "Building Docker images..."
docker-compose -f infra/docker/docker-compose.yml -f infra/docker/docker-compose.prod.yml build

# Start services
echo "Starting production services..."
docker-compose -f infra/docker/docker-compose.yml -f infra/docker/docker-compose.prod.yml up -d

echo "AI Marketing Agent System is now running in production mode!"
echo "Access the system status with: docker-compose -f infra/docker/docker-compose.yml -f infra/docker/docker-compose.prod.yml logs -f"