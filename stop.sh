#!/bin/bash

# Local AI Helper - Stop Script
# Usage: ./stop.sh [--volumes] [--clean]

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_header() {
    echo ""
    echo -e "${BLUE}╔══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║         🤖 Local AI Helper - Stop Script                 ║${NC}"
    echo -e "${BLUE}╚══════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check docker-compose command
check_docker_compose() {
    if command -v docker-compose &> /dev/null; then
        COMPOSE_CMD="docker-compose"
    elif docker compose version &> /dev/null; then
        COMPOSE_CMD="docker compose"
    else
        echo "docker-compose not found"
        exit 1
    fi
}

# Stop services
stop_services() {
    print_info "Stopping services..."
    $COMPOSE_CMD down
    print_success "Services stopped"
}

# Remove volumes (optional)
remove_volumes() {
    print_warning "Removing all data volumes (this will delete conversation history and downloaded models)!"
    read -p "Are you sure? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        $COMPOSE_CMD down -v
        print_success "Volumes removed"
    else
        print_info "Keeping volumes"
    fi
}

# Clean everything
full_clean() {
    print_warning "Removing containers, networks, AND volumes!"
    read -p "Are you sure? This will delete ALL data! (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        $COMPOSE_CMD down -v --remove-orphans
        docker network rm ai-helper-network 2>/dev/null || true
        print_success "Cleanup complete"
    else
        print_info "Cleanup cancelled"
    fi
}

# Main
main() {
    print_header
    check_docker_compose
    
    # Parse arguments
    if [[ "$1" == "--volumes" ]]; then
        stop_services
        remove_volumes
    elif [[ "$1" == "--clean" ]]; then
        full_clean
    else
        stop_services
        echo ""
        echo "To also remove volumes (delete all data):"
        echo -e "  ${YELLOW}./stop.sh --volumes${NC}"
        echo ""
        echo "For full cleanup including networks:"
        echo -e "  ${YELLOW}./stop.sh --clean${NC}"
    fi
    echo ""
}

main "$@"
