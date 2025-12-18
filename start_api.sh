#!/bin/bash
# Start Nexus-Mind API Server

echo "Starting Nexus-Mind API Server..."
echo "=================================="

# Check if Docker services are running
if ! docker ps | grep -q henry-chromadb; then
    echo "⚠️  ChromaDB not running. Starting Docker services..."
    docker-compose up -d
    sleep 5
fi

# Set Python path and start server
export PYTHONPATH=.:/Users/kolawoleojo/Library/Python/3.9/lib/python/site-packages

echo "Starting FastAPI server on port 8001..."
echo "API docs will be available at: http://localhost:8001/docs"
echo ""

python3 -m uvicorn src.server.api.main:app --host 0.0.0.0 --port 8001 --reload
