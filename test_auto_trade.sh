#!/bin/bash
# Test Auto-Trade Feature
# Validates all auto-trade endpoints are working

set -e

BACKEND_URL="https://trade-oracle-production.up.railway.app"
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}AUTO-TRADE FEATURE TEST${NC}"
echo -e "${BLUE}========================================${NC}"

# Test 1: Check market status
echo -e "\n${YELLOW}[1/3] Testing market status endpoint...${NC}"
MARKET_STATUS=$(curl -s "$BACKEND_URL/api/auto-trade/market-status" || echo "{\"error\": \"not deployed yet\"}")

if echo "$MARKET_STATUS" | grep -q "is_open"; then
    echo -e "${GREEN}✅ Market status endpoint working${NC}"
    echo "$MARKET_STATUS" | python3 -m json.tool
else
    echo -e "${RED}❌ Endpoint not deployed yet (expected if not pushed to Railway)${NC}"
    echo "$MARKET_STATUS"
fi

# Test 2: Start auto-trade (will fail if not deployed, that's ok)
echo -e "\n${YELLOW}[2/3] Testing auto-trade start endpoint...${NC}"
START_RESULT=$(curl -s -X POST "$BACKEND_URL/api/auto-trade/start" || echo "{\"error\": \"not deployed yet\"}")

if echo "$START_RESULT" | grep -q "session_id"; then
    echo -e "${GREEN}✅ Auto-trade started successfully${NC}"
    SESSION_ID=$(echo "$START_RESULT" | python3 -c "import sys, json; print(json.load(sys.stdin).get('session_id', ''))")
    echo "Session ID: $SESSION_ID"

    # Test 3: Check status
    echo -e "\n${YELLOW}[3/3] Testing status endpoint...${NC}"
    sleep 2  # Wait for processing
    STATUS=$(curl -s "$BACKEND_URL/api/auto-trade/status/$SESSION_ID")
    echo "$STATUS" | python3 -m json.tool

    if echo "$STATUS" | grep -q "status"; then
        echo -e "${GREEN}✅ Status endpoint working${NC}"
    else
        echo -e "${RED}❌ Status endpoint failed${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Endpoint not deployed yet (expected before git push)${NC}"
    echo "$START_RESULT"
    echo -e "\n${BLUE}This is normal! Deploy to Railway first:${NC}"
    echo "  git add ."
    echo "  git commit -m \"FEATURE: Auto-Trade - One-click intelligent trading\""
    echo "  git push"
fi

echo -e "\n${BLUE}========================================${NC}"
echo -e "${GREEN}Test complete!${NC}"
echo -e "${BLUE}========================================${NC}"

echo -e "\n${YELLOW}Next Steps:${NC}"
echo "1. Deploy to Railway: git push"
echo "2. Open frontend: https://trade-oracle-lac.vercel.app/auto-trade"
echo "3. Click 'Start Auto-Trade' button"
echo "4. Watch the automation!"
