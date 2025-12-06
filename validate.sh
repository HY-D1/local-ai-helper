#!/bin/bash
echo "🔍 Validating setup..."

# Check files exist
FILES=("docker-compose.yml" "Dockerfile" "requirements.txt" ".env" 
       "config/agent_configs.yaml" "scripts/init_db.sql")
for file in "${FILES[@]}"; do
    [ -f "$file" ] && echo "✅ $file" || echo "❌ Missing: $file"
done

# Check Docker running
docker info > /dev/null 2>&1 && echo "✅ Docker running" || echo "❌ Docker not running"

# Check containers
docker-compose ps

# Test API health
sleep 5
curl -s http://localhost:8000/health && echo "" && echo "✅ API healthy" || echo "❌ API not responding"
