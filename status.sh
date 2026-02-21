#!/bin/bash

# Local AI Helper - Status Check Script
# Usage: ./status.sh

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

API_URL="http://localhost:8000"
UI_URL="http://localhost:8501"

echo ""
echo -e "${BLUE}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║         🤖 Local AI Helper - Status Check                ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running${NC}"
    exit 1
fi

# Check containers
echo -e "${BLUE}Container Status:${NC}"
docker-compose ps 2>/dev/null || docker compose ps
echo ""

# Check API health
echo -n "API Health: "
if curl -s "$API_URL/health" | grep -q "healthy"; then
    echo -e "${GREEN}✅ Healthy${NC}"
else
    echo -e "${RED}❌ Unreachable${NC}"
fi

# Check UI
echo -n "UI Status:  "
if curl -s "$UI_URL" > /dev/null; then
    echo -e "${GREEN}✅ Ready${NC}"
else
    echo -e "${YELLOW}⚠️  Starting/Unhealthy${NC}"
fi

echo ""
echo -e "${BLUE}Quick Links:${NC}"
echo -e "  Web UI:   ${GREEN}$UI_URL${NC}"
echo -e "  API Docs: ${GREEN}$API_URL/docs${NC}"
echo -e "  Health:   ${GREEN}$API_URL/health${NC}"
echo ""
