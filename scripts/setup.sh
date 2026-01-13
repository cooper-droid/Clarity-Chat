#!/bin/bash

# Fiat Clarity Chat - Setup Script
# This script sets up the entire application

set -e

echo "======================================"
echo "Fiat Clarity Chat - Setup Script"
echo "======================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check for Docker
echo "Checking prerequisites..."
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed${NC}"
    echo "Please install Docker Desktop from https://www.docker.com/products/docker-desktop"
    exit 1
fi

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${RED}Error: Docker Compose is not installed${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Docker found${NC}"

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Python 3 found${NC}"

# Check for Node.js
if ! command -v node &> /dev/null; then
    echo -e "${RED}Error: Node.js is not installed${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Node.js found${NC}"
echo ""

# Start Docker containers
echo "Starting PostgreSQL with pgvector..."
docker compose up -d

echo "Waiting for database to be ready..."
sleep 5

echo -e "${GREEN}✓ Database started${NC}"
echo ""

# Setup backend
echo "Setting up Python backend..."
cd apps/api

if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

echo "Activating virtual environment..."
source .venv/bin/activate

echo "Installing Python dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

echo "Initializing database..."
python init_db.py

echo -e "${GREEN}✓ Backend setup complete${NC}"
echo ""

# Return to root
cd ../..

# Setup frontend
echo "Setting up Next.js frontend..."
cd apps/web

if [ ! -d "node_modules" ]; then
    echo "Installing Node dependencies..."
    npm install --silent
fi

echo -e "${GREEN}✓ Frontend setup complete${NC}"
echo ""

# Return to root
cd ../..

# Ingest sample data
echo "Ingesting sample marketing content..."
cd apps/api
source .venv/bin/activate
cd ../..

python scripts/ingest.py
python scripts/approve.py

echo ""
echo -e "${GREEN}======================================"
echo "✅ Setup Complete!"
echo "======================================${NC}"
echo ""
echo "To start the application:"
echo ""
echo "1. Backend (in one terminal):"
echo "   cd apps/api"
echo "   source .venv/bin/activate"
echo "   uvicorn main:app --reload"
echo ""
echo "2. Frontend (in another terminal):"
echo "   cd apps/web"
echo "   npm run dev"
echo ""
echo "3. Open http://localhost:3000 in your browser"
echo ""
echo -e "${YELLOW}Note: Running in DEV MODE (no OpenAI API key)${NC}"
echo "To use OpenAI, add OPENAI_API_KEY to apps/api/.env"
echo ""
