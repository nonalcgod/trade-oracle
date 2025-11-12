#!/bin/bash
# Morning Pre-Market Checklist
# Run this at 9:00am ET before market open (9:30am)
#
# Purpose: Verify all systems are ready for your first paper trade

set -e  # Exit on any error

BACKEND_URL="https://trade-oracle-production.up.railway.app"
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}TRADE ORACLE - MORNING PRE-MARKET CHECK${NC}"
echo -e "${BLUE}Date: $(date)${NC}"
echo -e "${BLUE}========================================${NC}"

# Test 1: Backend Health
echo -e "\n${YELLOW}[1/8] Checking backend health...${NC}"
HEALTH=$(curl -s "$BACKEND_URL/health")
if echo "$HEALTH" | grep -q '"status":"healthy"'; then
    echo -e "${GREEN}✅ Backend is healthy${NC}"
    echo "$HEALTH" | python3 -m json.tool
else
    echo -e "${RED}❌ Backend is down! Check Railway logs${NC}"
    exit 1
fi

# Test 2: Check Account Balance
echo -e "\n${YELLOW}[2/8] Checking Alpaca account balance...${NC}"
PORTFOLIO=$(curl -s "$BACKEND_URL/api/execution/portfolio")
BALANCE=$(echo "$PORTFOLIO" | python3 -c "import sys, json; print(json.load(sys.stdin).get('total_equity', 0))")
echo -e "${GREEN}✅ Account Balance: \$${BALANCE}${NC}"
if (( $(echo "$BALANCE < 100000" | bc -l) )); then
    echo -e "${YELLOW}⚠️  Warning: Balance below \$100,000${NC}"
fi

# Test 3: Verify No Open Positions (Fresh Start)
echo -e "\n${YELLOW}[3/8] Checking for open positions...${NC}"
POSITIONS=$(curl -s "$BACKEND_URL/api/execution/positions")
OPEN_COUNT=$(echo "$POSITIONS" | python3 -c "import sys, json; print(len([p for p in json.load(sys.stdin) if p.get('status') == 'open']))")
if [ "$OPEN_COUNT" -eq 0 ]; then
    echo -e "${GREEN}✅ No open positions (clean slate)${NC}"
else
    echo -e "${YELLOW}⚠️  Warning: $OPEN_COUNT open position(s) found${NC}"
    echo "$POSITIONS" | python3 -m json.tool
fi

# Test 4: Check Position Monitor
echo -e "\n${YELLOW}[4/8] Checking position monitor...${NC}"
MONITOR=$(curl -s "$BACKEND_URL/api/testing/monitor-status")
RUNNING=$(echo "$MONITOR" | python3 -c "import sys, json; print(json.load(sys.stdin).get('monitor_running', False))")
if [ "$RUNNING" == "True" ]; then
    echo -e "${GREEN}✅ Position monitor is running${NC}"
else
    echo -e "${RED}❌ Position monitor is NOT running!${NC}"
    exit 1
fi

# Test 5: Check VIX Level (for IV strategy)
echo -e "\n${YELLOW}[5/8] Checking VIX level...${NC}"
# Note: This will work during market hours
VIX_DATA=$(curl -s "$BACKEND_URL/api/data/latest/VIX" || echo '{"error": "Market closed or VIX unavailable"}')
if echo "$VIX_DATA" | grep -q '"symbol":"VIX"'; then
    VIX_PRICE=$(echo "$VIX_DATA" | python3 -c "import sys, json; print(json.load(sys.stdin).get('last_price', 'N/A'))")
    echo -e "${GREEN}✅ VIX: $VIX_PRICE${NC}"

    if (( $(echo "$VIX_PRICE > 20" | bc -l) )); then
        echo -e "${GREEN}   → High IV environment (good for IV Mean Reversion)${NC}"
    else
        echo -e "${YELLOW}   → Low IV environment (consider Iron Condor or Momentum)${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  VIX data not available (market may not be open yet)${NC}"
fi

# Test 6: Test Iron Condor Entry Window
echo -e "\n${YELLOW}[6/8] Checking Iron Condor entry window...${NC}"
IC_WINDOW=$(curl -s "$BACKEND_URL/api/iron-condor/should-enter")
SHOULD_ENTER=$(echo "$IC_WINDOW" | python3 -c "import sys, json; print(json.load(sys.stdin).get('should_enter', False))")
if [ "$SHOULD_ENTER" == "True" ]; then
    echo -e "${GREEN}✅ Iron Condor entry window is OPEN (9:31-9:45am)${NC}"
else
    REASON=$(echo "$IC_WINDOW" | python3 -c "import sys, json; print(json.load(sys.stdin).get('reason', 'Outside entry window'))")
    echo -e "${YELLOW}⚠️  Iron Condor entry window closed: $REASON${NC}"
fi

# Test 7: Test Momentum Scalping Scanner
echo -e "\n${YELLOW}[7/8] Scanning for momentum signals...${NC}"
MOMENTUM=$(curl -s "$BACKEND_URL/api/momentum-scalping/scan?symbols=SPY,QQQ")
SIGNAL_COUNT=$(echo "$MOMENTUM" | python3 -c "import sys, json; print(len(json.load(sys.stdin).get('signals', [])))")
echo -e "${GREEN}✅ Momentum scan complete: $SIGNAL_COUNT signal(s) found${NC}"
if [ "$SIGNAL_COUNT" -gt 0 ]; then
    echo "$MOMENTUM" | python3 -m json.tool
fi

# Test 8: Risk Management Status
echo -e "\n${YELLOW}[8/8] Checking risk management circuit breakers...${NC}"
CIRCUIT_BREAKERS=$(curl -s "$BACKEND_URL/api/risk/circuit-breakers" || echo '{}')
if echo "$CIRCUIT_BREAKERS" | grep -q 'max_portfolio_risk'; then
    echo -e "${GREEN}✅ Circuit breakers configured${NC}"
    echo "$CIRCUIT_BREAKERS" | python3 -m json.tool
else
    echo -e "${YELLOW}⚠️  Circuit breaker status unavailable${NC}"
fi

# Summary
echo -e "\n${BLUE}========================================${NC}"
echo -e "${BLUE}PRE-MARKET CHECKLIST COMPLETE${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}✅ All critical systems operational${NC}"
echo -e "\n${YELLOW}RECOMMENDED FIRST TRADE STRATEGIES:${NC}"
echo -e "${BLUE}1. IV Mean Reversion (if VIX > 20)${NC}"
echo -e "${BLUE}2. Iron Condor (9:31-9:45am window)${NC}"
echo -e "${BLUE}3. Momentum Scalping (if 6 conditions met)${NC}"
echo -e "\n${YELLOW}Next Steps:${NC}"
echo -e "1. Wait for market open (9:30am ET)"
echo -e "2. Run: ${BLUE}./execute_first_trade.sh${NC}"
echo -e "3. Monitor position in dashboard: ${BLUE}https://trade-oracle-lac.vercel.app${NC}"
echo -e "${BLUE}========================================${NC}"
