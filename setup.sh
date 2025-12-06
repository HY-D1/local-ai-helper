#!/bin/bash
set -e

echo "🚀 Setting up Local AI Helper..."

mkdir -p src/api/routers src/agents src/memory src/ui config scripts tests data/{raw,processed} models
touch data/raw/.gitkeep data/processed/.gitkeep models/.gitkeep

if [ ! -f .env ]; then
    cp .env.example .env
    echo "✅ .env created"
fi

if [ ! -d .git ]; then
    git init
    echo "✅ Git initialized"
fi

echo "✨ Setup complete!"
