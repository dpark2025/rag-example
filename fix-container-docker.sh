#!/bin/bash

echo "🔧 Fixing Docker container name conflict (Alternative)..."

# Stop and remove the existing container
echo "Stopping and removing existing local-rag-app container..."
docker stop local-rag-app 2>/dev/null || echo "Container was not running"
docker rm local-rag-app 2>/dev/null || echo "Container did not exist"

# Clean up any related containers
echo "Cleaning up any related containers..."
docker-compose -f docker-compose.docker.yml down 2>/dev/null || echo "No compose services to stop"

# Now start fresh
echo "Starting fresh containers with Docker..."
docker-compose -f docker-compose.docker.yml up -d

echo "✅ Docker container issue fixed!"
echo "Check status with: docker-compose -f docker-compose.docker.yml ps"