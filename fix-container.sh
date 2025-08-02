#!/bin/bash

echo "🔧 Fixing Podman container name conflict (Default)..."

# Stop and remove the existing container
echo "Stopping and removing existing local-rag-app container..."
podman stop local-rag-app 2>/dev/null || echo "Container was not running"
podman rm local-rag-app 2>/dev/null || echo "Container did not exist"

# Clean up any related containers
echo "Cleaning up any related containers..."
podman-compose down 2>/dev/null || echo "No compose services to stop"

# Now start fresh
echo "Starting fresh containers with Podman..."
podman-compose up -d

echo "✅ Podman container issue fixed!"
echo "Check status with: podman-compose ps"