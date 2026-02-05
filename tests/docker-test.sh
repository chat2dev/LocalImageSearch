#!/bin/bash
# Docker deployment verification script for Image Auto-Tagging System
# This script follows the README.md installation instructions step-by-step

set -e

echo "============================================"
echo "Docker Deployment Verification"
echo "Image Auto-Tagging System"
echo "============================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print colored messages
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}➜ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Check if Docker is installed
print_info "Checking Docker installation..."
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    echo "Visit: https://docs.docker.com/get-docker/"
    exit 1
fi
print_success "Docker is installed"

# Check if Docker Compose is installed
print_info "Checking Docker Compose installation..."
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi
print_success "Docker Compose is installed"

# Clean up any existing containers
print_info "Cleaning up existing containers..."
docker-compose down -v 2>/dev/null || true
print_success "Cleanup complete"

# Build and start services
print_info "Building Docker images (this may take a few minutes)..."
docker-compose build --no-cache

print_info "Starting services..."
docker-compose up -d

echo ""
echo "============================================"
echo "Waiting for services to be ready..."
echo "This includes:"
echo "  1. Starting Ollama service"
echo "  2. Downloading qwen3-vl:4b model (~3.3GB)"
echo "  3. Running deployment verification tests"
echo ""
echo "Monitoring logs for 5 minutes (or until completion)..."
echo "============================================"
echo ""

# Follow logs with timeout (5 minutes = 300 seconds)
print_info "Following application logs (timeout: 5 minutes)..."
echo ""

# Use timeout to limit log following
timeout 300 docker-compose logs -f app || {
    exit_code=$?
    if [ $exit_code -eq 124 ]; then
        echo ""
        print_info "Timeout reached (5 minutes)"
    fi
}

echo ""
echo "============================================"
print_info "Checking container status..."
echo ""

# Check if containers are still running
if docker ps | grep -q "image-tagger-app"; then
    print_success "Application container is running"
else
    print_error "Application container stopped unexpectedly"
    docker-compose logs --tail 50 app
    exit 1
fi

if docker ps | grep -q "image-tagger-ollama"; then
    print_success "Ollama container is running"
else
    print_error "Ollama container stopped unexpectedly"
fi

echo ""
print_success "Deployment verification complete!"
echo ""
echo "NOTE: Containers are still running. To stop them, run:"
echo "  docker-compose down"
echo ""
echo "To view logs again, run:"
echo "  docker-compose logs app"
echo ""
