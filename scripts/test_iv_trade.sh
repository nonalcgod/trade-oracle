#!/bin/bash

##############################################################################
# Trade Oracle - IV Mean Reversion Trade Test Script
#
# Automated end-to-end test of the full trading workflow:
# 1. Backend health check
# 2. Generate IV signal
# 3. Get risk approval
# 4. Execute trade
# 5. Verify execution
#
# Usage: ./scripts/test_iv_trade.sh [symbol] [quantity]
# Example: ./scripts/test_iv_trade.sh SPY251219C00600000 1
##############################################################################

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
API_BASE="${API_BASE:-https://trade-oracle-production.up.railway.app}"
SYMBOL="${1:-SPY251219C00600000}"
QUANTITY="${2:-1}"

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║          Trade Oracle - IV Mean Reversion Test            ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}Configuration:${NC}"
echo -e "  API Base: ${API_BASE}"
echo -e "  Symbol:   ${SYMBOL}"
echo -e "  Quantity: ${QUANTITY}"
echo ""

# Step 1: Health Check
echo -e "${BLUE}[1/5] Checking backend health...${NC}"
HEALTH=$(curl -s "${API_BASE}/health")
STATUS=$(echo "$HEALTH" | python3 -c "import sys, json; print(json.load(sys.stdin).get('status', 'unknown'))")

if [ "$STATUS" != "healthy" ]; then
    echo -e "${RED}✗ Backend unhealthy: $HEALTH${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Backend healthy${NC}"
echo ""

# Step 2: Generate Signal
echo -e "${BLUE}[2/5] Generating IV Mean Reversion signal...${NC}"
SIGNAL_RESPONSE=$(curl -s -X POST "${API_BASE}/api/strategies/signal" \
  -H 'Content-Type: application/json' \
  -d '{
    "tick": {
      "symbol": "'"${SYMBOL}"'",
      "underlying_price": 597.50,
      "strike": 600,
      "expiration": "2025-12-19T21:00:00.000Z",
      "bid": 11.80,
      "ask": 12.20,
      "delta": 0.48,
      "gamma": 0.015,
      "theta": -0.25,
      "vega": 0.18,
      "iv": 0.185,
      "timestamp": "2025-11-06T20:30:00.000Z"
    }
  }')

SIGNAL_TYPE=$(echo "$SIGNAL_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('signal', {}).get('signal', 'none'))" 2>/dev/null || echo "error")

if [ "$SIGNAL_TYPE" != "buy" ] && [ "$SIGNAL_TYPE" != "sell" ]; then
    echo -e "${RED}✗ No valid signal generated${NC}"
    echo "$SIGNAL_RESPONSE" | python3 -m json.tool
    exit 1
fi

# Extract signal details
ENTRY_PRICE=$(echo "$SIGNAL_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['signal']['entry_price'])")
STOP_LOSS=$(echo "$SIGNAL_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['signal']['stop_loss'])")
TAKE_PROFIT=$(echo "$SIGNAL_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['signal']['take_profit'])")
REASONING=$(echo "$SIGNAL_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['signal']['reasoning'])")

echo -e "${GREEN}✓ Signal generated: $(echo ${SIGNAL_TYPE} | tr '[:lower:]' '[:upper:]')${NC}"
echo -e "  Entry:       \$${ENTRY_PRICE}"
echo -e "  Stop Loss:   \$${STOP_LOSS}"
echo -e "  Take Profit: \$${TAKE_PROFIT}"
echo -e "  Reasoning:   ${REASONING}"
echo ""

# Step 3: Get Portfolio State
echo -e "${BLUE}[3/5] Fetching portfolio state...${NC}"
PORTFOLIO=$(curl -s "${API_BASE}/api/execution/portfolio")
BALANCE=$(echo "$PORTFOLIO" | python3 -c "import sys, json; print(json.load(sys.stdin)['portfolio']['balance'])")
DAILY_PNL=$(echo "$PORTFOLIO" | python3 -c "import sys, json; print(json.load(sys.stdin)['portfolio']['daily_pnl'])")

echo -e "${GREEN}✓ Portfolio retrieved${NC}"
echo -e "  Balance:    \$${BALANCE}"
echo -e "  Daily P&L:  \$${DAILY_PNL}"
echo ""

# Step 4: Get Risk Approval
echo -e "${BLUE}[4/5] Getting risk approval...${NC}"
RISK_RESPONSE=$(curl -s -X POST "${API_BASE}/api/risk/approve" \
  -H 'Content-Type: application/json' \
  -d '{
    "signal": '"$(echo "$SIGNAL_RESPONSE" | python3 -c "import sys, json; print(json.dumps(json.load(sys.stdin)['signal']))")"',
    "quantity": '"${QUANTITY}"',
    "portfolio": '"$(echo "$PORTFOLIO" | python3 -c "import sys, json; print(json.dumps(json.load(sys.stdin)['portfolio']))")"'
  }')

APPROVED=$(echo "$RISK_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('approved', False))" 2>/dev/null || echo "false")

if [ "$APPROVED" != "True" ]; then
    echo -e "${RED}✗ Trade not approved${NC}"
    echo "$RISK_RESPONSE" | python3 -m json.tool
    exit 1
fi

APPROVED_QTY=$(echo "$RISK_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('position_size', 0))")
MAX_LOSS=$(echo "$RISK_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('max_loss', '0'))")

echo -e "${GREEN}✓ Risk approved${NC}"
echo -e "  Approved Qty: ${APPROVED_QTY} contracts"
echo -e "  Max Loss:     \$${MAX_LOSS}"
echo ""

# Step 5: Execute Trade
echo -e "${BLUE}[5/5] Executing trade...${NC}"

# Calculate position size for approval
POSITION_SIZE=$(python3 -c "print(float('${ENTRY_PRICE}') * 100 * ${QUANTITY})")
RISK_AMOUNT=$(python3 -c "print(float('${ENTRY_PRICE}') * 100 * ${QUANTITY} * 0.5)")

EXECUTION_RESPONSE=$(curl -s -X POST "${API_BASE}/api/execution/order" \
  -H 'Content-Type: application/json' \
  -d '{
    "symbol": "'"${SYMBOL}"'",
    "side": "'"${SIGNAL_TYPE}"'",
    "quantity": '"${QUANTITY}"',
    "order_type": "market",
    "signal": {
      "symbol": "'"${SYMBOL}"'",
      "signal": "'"${SIGNAL_TYPE}"'",
      "signal_type": "'"${SIGNAL_TYPE}"'",
      "strategy": "iv_mean_reversion",
      "confidence": 1.0,
      "entry_price": "'"${ENTRY_PRICE}"'",
      "stop_loss": "'"${STOP_LOSS}"'",
      "take_profit": "'"${TAKE_PROFIT}"'",
      "reasoning": "'"${REASONING}"'",
      "timestamp": "'"$(date -u +"%Y-%m-%dT%H:%M:%S.000Z")"'"
    },
    "approval": {
      "approved": true,
      "position_size": '"${POSITION_SIZE}"',
      "risk_amount": '"${RISK_AMOUNT}"',
      "max_portfolio_risk": 0.02,
      "current_portfolio_risk": 0.019,
      "max_loss": "'"${MAX_LOSS}"'",
      "reasoning": "Automated test - risk approved for '"${QUANTITY}"' contract(s)"
    }
  }')

SUCCESS=$(echo "$EXECUTION_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('success', False))" 2>/dev/null || echo "false")

echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
if [ "$SUCCESS" == "True" ]; then
    ORDER_ID=$(echo "$EXECUTION_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('alpaca_order_id', 'N/A'))")
    echo -e "${GREEN}║                    ✓ TRADE EXECUTED                       ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${GREEN}Trade Details:${NC}"
    echo -e "  Symbol:      ${SYMBOL}"
    echo -e "  Side:        $(echo ${SIGNAL_TYPE} | tr '[:lower:]' '[:upper:]')"
    echo -e "  Quantity:    ${QUANTITY} contract(s)"
    echo -e "  Entry:       \$${ENTRY_PRICE}"
    echo -e "  Stop Loss:   \$${STOP_LOSS}"
    echo -e "  Take Profit: \$${TAKE_PROFIT}"
    echo -e "  Order ID:    ${ORDER_ID}"
    echo ""
    echo -e "${YELLOW}Next Steps:${NC}"
    echo -e "  1. Check dashboard: https://trade-oracle-lac.vercel.app"
    echo -e "  2. View position: ${API_BASE}/api/execution/positions"
    echo -e "  3. Monitor auto-exit at 50% profit or 75% loss"
    echo ""
else
    echo -e "${RED}║                    ✗ TRADE FAILED                         ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${RED}Error Details:${NC}"
    echo "$EXECUTION_RESPONSE" | python3 -m json.tool
    echo ""
    exit 1
fi
