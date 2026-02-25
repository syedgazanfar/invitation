#!/bin/bash

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║       Digital Invitation Platform - Startup Script        ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}[ERROR] Docker is not running! Please start Docker first.${NC}"
    exit 1
fi

echo -e "${YELLOW}[1/5]${NC} Checking environment files..."
if [ ! -f "apps/backend-python/.env" ]; then
    echo "Creating backend .env file..."
    cp apps/backend-python/.env.example apps/backend-python/.env
fi

if [ ! -f "apps/frontend-mui/.env.local" ]; then
    echo "Creating frontend .env file..."
    cp apps/frontend-mui/.env.example apps/frontend-mui/.env.local
fi

echo -e "${YELLOW}[2/5]${NC} Starting Docker containers..."
docker-compose down > /dev/null 2>&1
docker-compose up -d --build

if [ $? -ne 0 ]; then
    echo -e "${RED}[ERROR] Failed to start containers!${NC}"
    exit 1
fi

echo -e "${YELLOW}[3/5]${NC} Waiting for database to be ready..."
sleep 10

echo -e "${YELLOW}[4/5]${NC} Running database migrations..."
docker-compose exec backend python src/manage.py migrate

echo -e "${YELLOW}[5/5]${NC} Seeding database with initial data..."
docker-compose exec backend python src/manage.py seed_data

echo ""
echo -e "${GREEN}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║              Application Started Successfully!            ║${NC}"
echo -e "${GREEN}╠═══════════════════════════════════════════════════════════╣${NC}"
echo -e "${GREEN}║                                                           ║${NC}"
echo -e "${GREEN}║  Frontend: http://localhost:3000                          ║${NC}"
echo -e "${GREEN}║  Backend API: http://localhost:8000                       ║${NC}"
echo -e "${GREEN}║  Admin Panel: http://localhost:8000/admin                 ║${NC}"
echo -e "${GREEN}║                                                           ║${NC}"
echo -e "${GREEN}║  Create admin user:                                       ║${NC}"
echo -e "${GREEN}║  docker-compose exec backend python src/manage.py         ║${NC}"
echo -e "${GREEN}║  createsuperuser                                          ║${NC}"
echo -e "${GREEN}║                                                           ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""
read -p "Press Enter to view logs (Ctrl+C to exit)..."
clear
docker-compose logs -f
