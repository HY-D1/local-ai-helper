#!/bin/bash
set -e

echo "🚀 Starting Local AI Helper..."

if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker not running"
    exit 1
fi

docker-compose up -d
echo "⏳ Waiting for services..."
sleep 15

echo "📥 Pulling default model..."
docker exec ai-helper-ollama ollama pull qwen2.5:7b

echo "✨ Started! Access at http://localhost:8501"
