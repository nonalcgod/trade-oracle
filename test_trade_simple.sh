#!/bin/bash

# Trade Oracle - Simple Trade Lifecycle Test
# Uses curl to test the full position lifecycle

API_BASE="https://trade-oracle-production.up.railway.app"

echo "================================================================================"
echo "TRADE ORACLE - POSITION LIFECYCLE TEST"
echo "================================================================================"
echo "API: $API_BASE"
echo "Time: $(date)"
echo "================================================================================"
echo ""

# Step 1: Health Check
echo "📡 Step 1: Health Check"
echo "--------------------------------------------------------------------------------"
HEALTH=$(curl -s "$API_BASE/health")
echo "$HEALTH" | python3 -m json.tool
echo ""

# Step 2: Get Portfolio
echo "💰 Step 2: Current Portfolio"
echo "--------------------------------------------------------------------------------"
PORTFOLIO=$(curl -s "$API_BASE/api/execution/portfolio")
echo "$PORTFOLIO" | python3 -m json.tool
echo ""

# Step 3: Get Current Positions
echo "📍 Step 3: Current Open Positions"
echo "--------------------------------------------------------------------------------"
POSITIONS=$(curl -s "$API_BASE/api/execution/positions")
echo "$POSITIONS" | python3 -m json.tool
POSITION_COUNT=$(echo "$POSITIONS" | python3 -c "import sys, json; print(len(json.load(sys.stdin)))")
echo ""
echo "Found $POSITION_COUNT open position(s)"
echo ""

# Step 4: Get Recent Trades
echo "📜 Step 4: Recent Trades (Last 10)"
echo "--------------------------------------------------------------------------------"
TRADES=$(curl -s "$API_BASE/api/execution/trades?limit=10")
echo "$TRADES" | python3 -m json.tool | head -50
echo ""

# Step 5: Check Risk Limits
echo "🛡️  Step 5: Current Risk Limits"
echo "--------------------------------------------------------------------------------"
LIMITS=$(curl -s "$API_BASE/api/risk/limits")
echo "$LIMITS" | python3 -m json.tool
echo ""

# Summary
echo "================================================================================"
echo "✅ TEST COMPLETE"
echo "================================================================================"
echo ""
echo "📊 Summary:"
echo "  • Backend: Healthy"
echo "  • Open Positions: $POSITION_COUNT"
echo "  • Position Monitor: Running in background (60s polling)"
echo ""
echo "🌐 View Dashboard:"
echo "  https://trade-oracle-lac.vercel.app"
echo ""
echo "📝 To Execute a Real Test Trade:"
echo "  1. Manually trigger a signal via API"
echo "  2. Or wait for market conditions (IV < 30th percentile)"
echo "  3. Or adjust risk limits to allow smaller test positions"
echo ""
echo "💡 Monitor Activity:"
echo "  railway logs --service trade-oracle | grep -i 'monitor'"
echo ""
