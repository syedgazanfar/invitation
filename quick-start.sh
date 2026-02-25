#!/bin/bash

# Wedding Invitations Platform - Quick Start Script
# This script automates the setup and deployment process

set -e  # Exit on any error

echo "========================================="
echo "  Wedding Invitations Platform"
echo "  Quick Start Setup"
echo "========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Check if Docker is installed
check_docker() {
    echo "Checking Docker installation..."
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    print_success "Docker is installed"

    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    print_success "Docker Compose is installed"
}

# Stop existing containers
stop_containers() {
    echo ""
    echo "Stopping existing containers (if any)..."
    docker-compose down -v 2>/dev/null || true
    print_success "Stopped existing containers"
}

# Clean Docker cache (optional)
clean_cache() {
    echo ""
    read -p "Do you want to clean Docker cache? This will remove all unused images. (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Cleaning Docker cache..."
        docker system prune -a -f
        print_success "Docker cache cleaned"
    else
        print_warning "Skipping cache cleanup"
    fi
}

# Build containers
build_containers() {
    echo ""
    echo "Building Docker containers (this may take a few minutes)..."
    docker-compose build --no-cache
    print_success "Containers built successfully"
}

# Start containers
start_containers() {
    echo ""
    echo "Starting containers..."
    docker-compose up -d
    print_success "Containers started"
}

# Wait for services
wait_for_services() {
    echo ""
    echo "Waiting for services to be ready..."

    # Wait for database
    echo -n "Waiting for database"
    for i in {1..30}; do
        if docker-compose exec -T postgres pg_isready -U postgres &> /dev/null; then
            echo ""
            print_success "Database is ready"
            break
        fi
        echo -n "."
        sleep 1
    done

    # Wait for backend
    echo -n "Waiting for backend"
    for i in {1..30}; do
        if curl -s http://localhost:9301/api/plans > /dev/null 2>&1; then
            echo ""
            print_success "Backend is ready"
            break
        fi
        echo -n "."
        sleep 1
    done

    # Wait for frontend
    echo -n "Waiting for frontend"
    for i in {1..30}; do
        if curl -s http://localhost:9300 > /dev/null 2>&1; then
            echo ""
            print_success "Frontend is ready"
            break
        fi
        echo -n "."
        sleep 1
    done
}

# Verify setup
verify_setup() {
    echo ""
    echo "Verifying setup..."

    # Check containers
    if [ $(docker-compose ps | grep -c "Up") -eq 3 ]; then
        print_success "All containers are running"
    else
        print_error "Some containers are not running"
        docker-compose ps
        exit 1
    fi

    # Check database
    if docker-compose exec -T postgres psql -U postgres -d wedding_invitations -c "SELECT COUNT(*) FROM plans;" | grep -q "3"; then
        print_success "Database is seeded correctly"
    else
        print_warning "Database might not be seeded. Running seed..."
        docker-compose exec -T backend npm run seed
    fi
}

# Display access information
display_info() {
    echo ""
    echo "========================================="
    echo "  Setup Complete!"
    echo "========================================="
    echo ""
    echo "Access your application:"
    echo ""
    echo "  Frontend:  http://localhost:9300"
    echo "  Backend:   http://localhost:9301/api"
    echo "  Database:  localhost:5432"
    echo ""
    echo "Database credentials:"
    echo "  Username:  postgres"
    echo "  Password:  postgres"
    echo "  Database:  wedding_invitations"
    echo ""
    echo "Quick commands:"
    echo "  View logs:       docker-compose logs -f"
    echo "  Stop services:   docker-compose down"
    echo "  Restart:         docker-compose restart"
    echo ""
    echo "Next steps:"
    echo "  1. Open http://localhost:9300 in your browser"
    echo "  2. Click 'Sign Up' to create an account"
    echo "  3. Create your first wedding event"
    echo "  4. Share the invitation URL with guests"
    echo ""
    echo "For more information, see:"
    echo "  - SETUP.md for detailed setup instructions"
    echo "  - TESTING_GUIDE.md for testing scenarios"
    echo "  - TROUBLESHOOTING.md for common issues"
    echo ""
    print_success "Happy wedding planning!"
}

# Main execution
main() {
    check_docker
    stop_containers
    clean_cache
    build_containers
    start_containers
    wait_for_services
    verify_setup
    display_info
}

# Run main function
main
