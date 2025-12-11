#!/bin/bash
# Quick Start Script for Payment Analytics Project
# This script sets up and runs the entire analytics pipeline

set -e  # Exit on error

echo "======================================================================"
echo "PAYMENT ANALYTICS - QUICK START"
echo "======================================================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}✗ Docker is not running. Please start Docker and try again.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Docker is running${NC}"

# Check if UV is installed
if ! command -v uv &> /dev/null; then
    echo -e "${RED}✗ UV is not installed. Please install it first:${NC}"
    echo "  brew install uv  # On macOS"
    exit 1
fi

echo -e "${GREEN}✓ UV package manager found${NC}"

# Step 1: Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo ""
    echo "Creating Python virtual environment..."
    uv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
fi

# Step 2: Install dependencies
echo ""
echo "Installing Python dependencies..."
uv pip install pandas numpy sqlalchemy psycopg2-binary pyarrow python-dotenv
echo -e "${GREEN}✓ Dependencies installed${NC}"

# Step 3: Process data if not already done
if [ ! -f "data/processed/payments_enriched.parquet" ]; then
    echo ""
    echo "Processing data..."
    echo "  → Step 1/2: Cleaning data..."
    .venv/bin/python src/01_clean_data.py
    
    echo "  → Step 2/2: Enriching data..."
    .venv/bin/python src/02_enrich_data.py
    
    echo -e "${GREEN}✓ Data processing complete${NC}"
else
    echo -e "${YELLOW}⚠ Data already processed (skipping)${NC}"
fi

# Step 4: Start Docker services
echo ""
echo "Starting PostgreSQL and Metabase..."
docker-compose up -d

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL to be ready..."
sleep 5

# Check if database is ready
until docker-compose exec -T postgres pg_isready -U analytics_user > /dev/null 2>&1; do
    echo "  Waiting for PostgreSQL..."
    sleep 2
done
echo -e "${GREEN}✓ PostgreSQL is ready${NC}"

# Step 5: Load data to database
echo ""
echo "Loading data to PostgreSQL..."
.venv/bin/python src/03_load_to_db.py

# Step 6: Wait for Metabase to be ready
echo ""
echo "Waiting for Metabase to start (this may take 1-2 minutes)..."
sleep 10

# Check if Metabase is responding
MAX_RETRIES=30
RETRY_COUNT=0
until curl -s http://localhost:3000 > /dev/null || [ $RETRY_COUNT -eq $MAX_RETRIES ]; do
    echo "  Waiting for Metabase... ($RETRY_COUNT/$MAX_RETRIES)"
    sleep 5
    RETRY_COUNT=$((RETRY_COUNT + 1))
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo -e "${YELLOW}⚠ Metabase is taking longer than expected to start${NC}"
    echo "  Check status with: docker-compose logs metabase"
else
    echo -e "${GREEN}✓ Metabase is running${NC}"
fi

# Summary
echo ""
echo "======================================================================"
echo -e "${GREEN}✓ SETUP COMPLETE!${NC}"
echo "======================================================================"
echo ""
echo "Next steps:"
echo "  1. Open Metabase: http://localhost:3000"
echo "  2. Complete initial setup (see dashboards/METABASE_SETUP.md)"
echo "  3. Database credentials:"
echo "       Host: postgres (or localhost from your machine)"
echo "       Port: 5432"
echo "       Database: payments_analytics"
echo "       User: proton"
echo "       Password: proton_analytics_2024"
echo ""
echo "Useful commands:"
echo "  - Check services: docker-compose ps"
echo "  - View logs: docker-compose logs -f"
echo "  - Stop services: docker-compose down"
echo "  - Restart: docker-compose restart"
echo ""
echo "======================================================================"
