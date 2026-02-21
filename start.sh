#!/bin/bash

# Local AI Helper - Startup Script
# Usage: ./start.sh [--no-browser]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
API_URL="http://localhost:8000"
UI_URL="http://localhost:8501"
MAX_RETRIES=30
RETRY_DELAY=2

# Parse arguments
OPEN_BROWSER=true
if [[ "$1" == "--no-browser" ]]; then
    OPEN_BROWSER=false
fi

# Helper functions
print_header() {
    echo ""
    echo -e "${BLUE}╔══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║         🤖 Local AI Helper - Startup Script              ║${NC}"
    echo -e "${BLUE}╚══════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if Docker is running
check_docker() {
    print_info "Checking Docker..."
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker Desktop first."
        exit 1
    fi
    print_success "Docker is running"
}

# Check if docker-compose is available
check_docker_compose() {
    if command -v docker-compose &> /dev/null; then
        COMPOSE_CMD="docker-compose"
    elif docker compose version &> /dev/null; then
        COMPOSE_CMD="docker compose"
    else
        print_error "docker-compose not found. Please install Docker Compose."
        exit 1
    fi
}

# Create Docker network if needed
setup_network() {
    if ! docker network ls | grep -q "ai-helper-network"; then
        print_info "Creating Docker network..."
        docker network create ai-helper-network
    fi
}

# Start services
start_services() {
    print_info "Starting services..."
    $COMPOSE_CMD up -d
    print_success "Services started"
}

# Wait for service to be healthy
wait_for_service() {
    local service_name=$1
    local url=$2
    local retry=0
    
    echo -n "Waiting for $service_name"
    while [ $retry -lt $MAX_RETRIES ]; do
        if curl -s "$url" > /dev/null 2>&1; then
            echo ""
            print_success "$service_name is ready"
            return 0
        fi
        echo -n "."
        sleep $RETRY_DELAY
        retry=$((retry + 1))
    done
    echo ""
    return 1
}

# Check all services health
check_health() {
    print_info "Checking service health..."
    
    # Check API
    if ! wait_for_service "API" "$API_URL/health"; then
        print_error "API failed to start. Check logs with: $COMPOSE_CMD logs api"
        return 1
    fi
    
    # Check UI (Streamlit takes longer)
    echo -n "Waiting for UI"
    retry=0
    while [ $retry -lt $MAX_RETRIES ]; do
        if curl -s "$UI_URL" > /dev/null 2>&1; then
            echo ""
            print_success "UI is ready"
            return 0
        fi
        echo -n "."
        sleep $RETRY_DELAY
        retry=$((retry + 1))
    done
    echo ""
    print_warning "UI is still starting (this is normal for first run)"
    return 0
}

# Display status
display_status() {
    echo ""
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    print_success "All systems operational!"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo ""
    
    # Get container status
    echo -e "${BLUE}Container Status:${NC}"
    $COMPOSE_CMD ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || $COMPOSE_CMD ps
    echo ""
    
    # Display URLs
    echo -e "${BLUE}Access Points:${NC}"
    echo -e "  🌐 Web UI:     ${GREEN}$UI_URL${NC}"
    echo -e "  🔌 API Docs:   ${GREEN}$API_URL/docs${NC}"
    echo -e "  💓 Health:     ${GREEN}$API_URL/health${NC}"
    echo ""
}

# Open browser
open_browser() {
    if [ "$OPEN_BROWSER" = true ]; then
        print_info "Opening browser..."
        sleep 2
        if [[ "$OSTYPE" == "darwin"* ]]; then
            open "$UI_URL"
        elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
            xdg-open "$UI_URL" 2>/dev/null || sensible-browser "$UI_URL" 2>/dev/null || echo "Please open $UI_URL manually"
        else
            start "$UI_URL" 2>/dev/null || echo "Please open $UI_URL manually"
        fi
    fi
}

# Show next steps
show_next_steps() {
    echo -e "${BLUE}Quick Start Guide:${NC}"
    echo ""
    echo "1. Download a model (first time only):"
    echo -e "   → Open ${YELLOW}$UI_URL${NC}"
    echo -e "   → Click ${YELLOW}'📦 Download Models'${NC} in the sidebar"
    echo -e "   → Download ${YELLOW}'Llama 3.2 (3B)'${NC} (~2GB, takes 5-10 min)"
    echo ""
    echo "2. Start chatting:"
    echo -e "   → Select an agent mode: ${YELLOW}💬 General, 🔢 Math, 💻 Code, ✍️ Writing, 🎨 Design${NC}"
    echo -e "   → Type a message and press Enter"
    echo -e "   → Memory is ${GREEN}ON${NC} by default"
    echo ""
    echo "3. Useful commands:"
    echo -e "   ${YELLOW}./test_features.sh${NC}   - Run smoke tests"
    echo -e "   ${YELLOW}./stop.sh${NC}            - Stop all services"
    echo -e "   ${YELLOW}$COMPOSE_CMD logs -f${NC}  - View logs"
    echo ""
}

# Main execution
main() {
    print_header
    
    # Check prerequisites
    check_docker
    check_docker_compose
    
    # Setup and start
    setup_network
    start_services
    
    # Wait for services
    if check_health; then
        display_status
        open_browser
        show_next_steps
    else
        print_error "Some services failed to start."
        echo "Check logs with: $COMPOSE_CMD logs"
        exit 1
    fi
}

# Run main function
main "$@"
