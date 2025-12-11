#!/bin/bash
# Service Status Checker for Payment Analytics

echo "======================================================================"
echo "PAYMENT ANALYTICS - SERVICE STATUS"
echo "======================================================================"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check Docker
echo ""
echo "Docker:"
if docker info > /dev/null 2>&1; then
    echo -e "  ${GREEN}✓${NC} Docker is running"
else
    echo -e "  ${RED}✗${NC} Docker is not running"
fi

# Check containers
echo ""
echo "Containers:"
if docker-compose ps | grep -q "payment-analytics-db"; then
    DB_STATUS=$(docker-compose ps | grep payment-analytics-db | awk '{print $6}')
    if [ "$DB_STATUS" = "running" ]; then
        echo -e "  ${GREEN}✓${NC} PostgreSQL is running"
        
        # Check if database is accessible
        if docker-compose exec -T postgres pg_isready -U proton > /dev/null 2>&1; then
            echo -e "  ${GREEN}✓${NC} PostgreSQL is accepting connections"
            
            # Check record count
            RECORD_COUNT=$(docker-compose exec -T postgres psql -U proton -d payments_analytics -t -c "SELECT COUNT(*) FROM payments;" 2>/dev/null | tr -d ' ')
            if [ ! -z "$RECORD_COUNT" ]; then
                echo -e "  ${GREEN}✓${NC} Database contains $RECORD_COUNT records"
            fi
        else
            echo -e "  ${YELLOW}⚠${NC} PostgreSQL is not ready yet"
        fi
    else
        echo -e "  ${RED}✗${NC} PostgreSQL is not running"
    fi
else
    echo -e "  ${RED}✗${NC} PostgreSQL container not found"
fi

if docker-compose ps | grep -q "payment-analytics-metabase"; then
    MB_STATUS=$(docker-compose ps | grep payment-analytics-metabase | awk '{print $6}')
    if [ "$MB_STATUS" = "running" ]; then
        echo -e "  ${GREEN}✓${NC} Metabase is running"
        
        # Check if Metabase is responding
        if curl -s http://localhost:3000 > /dev/null 2>&1; then
            echo -e "  ${GREEN}✓${NC} Metabase is accessible at http://localhost:3000"
        else
            echo -e "  ${YELLOW}⚠${NC} Metabase is starting up (may take 1-2 minutes)"
        fi
    else
        echo -e "  ${RED}✗${NC} Metabase is not running"
    fi
else
    echo -e "  ${RED}✗${NC} Metabase container not found"
fi

# Check data files
echo ""
echo "Data Files:"
if [ -f "data/raw/subscription-billing.csv" ]; then
    LINES=$(wc -l < data/raw/subscription-billing.csv)
    echo -e "  ${GREEN}✓${NC} Raw data: $LINES lines"
else
    echo -e "  ${RED}✗${NC} Raw data not found"
fi

if [ -f "data/processed/payments_clean.parquet" ]; then
    echo -e "  ${GREEN}✓${NC} Cleaned data exists"
else
    echo -e "  ${YELLOW}⚠${NC} Cleaned data not found"
fi

if [ -f "data/processed/payments_proton.parquet" ]; then
    echo -e "  ${GREEN}✓${NC} Enriched data exists"
else
    echo -e "  ${YELLOW}⚠${NC} Enriched data not found"
fi

# Check Python environment
echo ""
echo "Python Environment:"
if [ -d ".venv" ]; then
    echo -e "  ${GREEN}✓${NC} Virtual environment exists"
    
    if .venv/bin/python -c "import pandas" 2>/dev/null; then
        echo -e "  ${GREEN}✓${NC} Dependencies installed"
    else
        echo -e "  ${YELLOW}⚠${NC} Dependencies not installed"
    fi
else
    echo -e "  ${RED}✗${NC} Virtual environment not found"
fi

echo ""
echo "======================================================================"
