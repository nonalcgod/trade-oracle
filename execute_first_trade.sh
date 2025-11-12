#!/bin/bash
# Execute First Paper Trade
# Interactive script to place your first trade with full performance tracking
#
# Usage: ./execute_first_trade.sh
# Time: Run between 9:30am - 11:30am ET

set -e

BACKEND_URL="https://trade-oracle-production.up.railway.app"
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}TRADE ORACLE - FIRST PAPER TRADE${NC}"
echo -e "${BLUE}========================================${NC}"

# Get portfolio balance
echo -e "\n${YELLOW}Fetching account balance...${NC}"
PORTFOLIO=$(curl -s "$BACKEND_URL/api/execution/portfolio")
BALANCE=$(echo "$PORTFOLIO" | python3 -c "import sys, json; print(json.load(sys.stdin).get('total_equity', 0))")
echo -e "${GREEN}Account Balance: \$${BALANCE}${NC}"

# Strategy Selection
echo -e "\n${CYAN}========================================${NC}"
echo -e "${CYAN}SELECT YOUR FIRST STRATEGY${NC}"
echo -e "${CYAN}========================================${NC}"
echo -e "${BLUE}1. IV Mean Reversion${NC} (Recommended if VIX > 20)"
echo -e "   - Single-leg options (30-45 DTE)"
echo -e "   - Buy low IV, sell high IV"
echo -e "   - 75% backtest win rate"
echo ""
echo -e "${BLUE}2. Iron Condor${NC} (Available 9:31-9:45am only)"
echo -e "   - 4-leg spread, same-day expiration"
echo -e "   - Profit from range-bound markets"
echo -e "   - 70-80% theoretical win rate"
echo ""
echo -e "${BLUE}3. Momentum Scalping${NC} (Most sophisticated)"
echo -e "   - 0DTE contracts, 6-condition system"
echo -e "   - Requires: EMA cross, RSI, volume spike, VWAP, etc."
echo -e "   - Max 4 trades/day, strict discipline"
echo ""
read -p "Enter strategy number (1, 2, or 3): " STRATEGY_CHOICE

case $STRATEGY_CHOICE in
    1)
        echo -e "\n${GREEN}Selected: IV Mean Reversion${NC}"
        echo -e "${YELLOW}Generating signal for SPY...${NC}"

        # Step 1: Generate IV signal
        SIGNAL=$(curl -s -X POST "$BACKEND_URL/api/strategies/signal" \
            -H "Content-Type: application/json" \
            -d '{
                "symbol": "SPY",
                "lookback_days": 90
            }')

        echo -e "${GREEN}Signal Generated:${NC}"
        echo "$SIGNAL" | python3 -m json.tool

        IV_SIGNAL=$(echo "$SIGNAL" | python3 -c "import sys, json; print(json.load(sys.stdin).get('signal', 'HOLD'))")
        IV_PERCENTILE=$(echo "$SIGNAL" | python3 -c "import sys, json; print(json.load(sys.stdin).get('iv_percentile', 0))")

        if [ "$IV_SIGNAL" == "HOLD" ]; then
            echo -e "\n${YELLOW}⚠️  Signal recommends HOLD (IV percentile: $IV_PERCENTILE)${NC}"
            echo -e "${YELLOW}No strong IV signal at this time.${NC}"
            echo -e "\n${BLUE}Options:${NC}"
            echo "1. Wait for better setup (recommended)"
            echo "2. Execute test trade anyway (for learning)"
            read -p "Continue? (y/n): " CONTINUE
            if [ "$CONTINUE" != "y" ]; then
                echo -e "${YELLOW}Trade cancelled. Smart decision!${NC}"
                exit 0
            fi
        fi

        # Step 2: Build order payload
        echo -e "\n${YELLOW}Building order payload...${NC}"
        read -p "Symbol (default SPY): " SYMBOL
        SYMBOL=${SYMBOL:-SPY}

        read -p "Option type (call/put, default call): " OPTION_TYPE
        OPTION_TYPE=${OPTION_TYPE:-call}

        read -p "Strike price (e.g., 580): " STRIKE
        read -p "Expiration (YYYY-MM-DD, e.g., 2025-12-16): " EXPIRATION
        read -p "Number of contracts (default 1): " CONTRACTS
        CONTRACTS=${CONTRACTS:-1}

        # Determine action from signal
        if [ "$IV_SIGNAL" == "BUY" ]; then
            ACTION="buy"
        elif [ "$IV_SIGNAL" == "SELL" ]; then
            ACTION="sell"
        else
            read -p "Action (buy/sell): " ACTION
        fi

        ORDER_PAYLOAD=$(cat <<EOF
{
    "symbol": "$SYMBOL",
    "option_type": "$OPTION_TYPE",
    "strike": $STRIKE,
    "expiration": "$EXPIRATION",
    "action": "$ACTION",
    "contracts": $CONTRACTS,
    "strategy": "iv_mean_reversion",
    "entry_reason": "FIRST LIVE PAPER TRADE - IV Signal: $IV_SIGNAL (Percentile: $IV_PERCENTILE)"
}
EOF
)

        echo -e "\n${CYAN}Order Payload:${NC}"
        echo "$ORDER_PAYLOAD" | python3 -m json.tool

        read -p "Execute this order? (y/n): " CONFIRM
        if [ "$CONFIRM" != "y" ]; then
            echo -e "${YELLOW}Order cancelled${NC}"
            exit 0
        fi

        # Step 3: Execute order
        echo -e "\n${YELLOW}Executing order...${NC}"
        RESULT=$(curl -s -X POST "$BACKEND_URL/api/execution/order" \
            -H "Content-Type: application/json" \
            -d "$ORDER_PAYLOAD")

        echo -e "\n${GREEN}Order Result:${NC}"
        echo "$RESULT" | python3 -m json.tool

        # Check if successful
        if echo "$RESULT" | grep -q '"order_id"'; then
            echo -e "\n${GREEN}✅ TRADE EXECUTED SUCCESSFULLY!${NC}"
            ORDER_ID=$(echo "$RESULT" | python3 -c "import sys, json; print(json.load(sys.stdin).get('order_id', 'N/A'))")
            echo -e "${GREEN}Order ID: $ORDER_ID${NC}"
        else
            echo -e "\n${RED}❌ Order failed. See error above.${NC}"
            exit 1
        fi
        ;;

    2)
        echo -e "\n${GREEN}Selected: Iron Condor${NC}"
        echo -e "${YELLOW}Checking entry window...${NC}"

        WINDOW_CHECK=$(curl -s "$BACKEND_URL/api/iron-condor/should-enter")
        SHOULD_ENTER=$(echo "$WINDOW_CHECK" | python3 -c "import sys, json; print(json.load(sys.stdin).get('should_enter', False))")

        if [ "$SHOULD_ENTER" != "True" ]; then
            echo -e "${RED}❌ Entry window closed (available 9:31-9:45am ET only)${NC}"
            REASON=$(echo "$WINDOW_CHECK" | python3 -c "import sys, json; print(json.load(sys.stdin).get('reason', 'N/A'))")
            echo -e "${YELLOW}Reason: $REASON${NC}"
            exit 1
        fi

        echo -e "${GREEN}✅ Entry window is OPEN${NC}"

        # Generate Iron Condor signal
        echo -e "\n${YELLOW}Generating Iron Condor signal...${NC}"
        SIGNAL=$(curl -s -X POST "$BACKEND_URL/api/iron-condor/signal" \
            -H "Content-Type: application/json" \
            -d '{"symbol": "SPY"}')

        echo "$SIGNAL" | python3 -m json.tool

        IC_SIGNAL=$(echo "$SIGNAL" | python3 -c "import sys, json; print(json.load(sys.stdin).get('signal', 'HOLD'))")

        if [ "$IC_SIGNAL" != "ENTER_IC" ]; then
            echo -e "\n${YELLOW}⚠️  No Iron Condor setup available${NC}"
            exit 0
        fi

        # Build Iron Condor
        echo -e "\n${YELLOW}Building Iron Condor structure...${NC}"
        IC_BUILD=$(curl -s -X POST "$BACKEND_URL/api/iron-condor/build" \
            -H "Content-Type: application/json" \
            -d '{"symbol": "SPY", "target_delta": 0.15}')

        echo "$IC_BUILD" | python3 -m json.tool

        read -p "Execute this Iron Condor? (y/n): " CONFIRM
        if [ "$CONFIRM" != "y" ]; then
            echo -e "${YELLOW}Order cancelled${NC}"
            exit 0
        fi

        # Execute multi-leg order
        echo -e "\n${YELLOW}Executing Iron Condor...${NC}"
        LEGS=$(echo "$IC_BUILD" | python3 -c "import sys, json; print(json.dumps(json.load(sys.stdin).get('legs', [])))")

        RESULT=$(curl -s -X POST "$BACKEND_URL/api/execution/order/multi-leg" \
            -H "Content-Type: application/json" \
            -d "{
                \"symbol\": \"SPY\",
                \"strategy\": \"iron_condor\",
                \"legs\": $LEGS,
                \"entry_reason\": \"FIRST IRON CONDOR TRADE\"
            }")

        echo "$RESULT" | python3 -m json.tool

        if echo "$RESULT" | grep -q '"position_id"'; then
            echo -e "\n${GREEN}✅ IRON CONDOR EXECUTED!${NC}"
        else
            echo -e "\n${RED}❌ Execution failed${NC}"
            exit 1
        fi
        ;;

    3)
        echo -e "\n${GREEN}Selected: Momentum Scalping${NC}"
        echo -e "${YELLOW}Scanning for 6-condition setups...${NC}"

        SCAN=$(curl -s "$BACKEND_URL/api/momentum-scalping/scan?symbols=SPY,QQQ")
        SIGNAL_COUNT=$(echo "$SCAN" | python3 -c "import sys, json; print(len(json.load(sys.stdin).get('signals', [])))")

        if [ "$SIGNAL_COUNT" -eq 0 ]; then
            echo -e "\n${YELLOW}⚠️  No momentum signals found (all 6 conditions must be met)${NC}"
            echo -e "${BLUE}Required conditions:${NC}"
            echo "  1. EMA(9) crosses EMA(21)"
            echo "  2. RSI(14) confirmation"
            echo "  3. Volume spike (≥2x average)"
            echo "  4. VWAP breakout"
            echo "  5. Relative strength"
            echo "  6. Time window (9:31-11:30am ET)"
            exit 0
        fi

        echo -e "${GREEN}✅ Found $SIGNAL_COUNT momentum signal(s)!${NC}"
        echo "$SCAN" | python3 -m json.tool

        # Get first signal
        FIRST_SIGNAL=$(echo "$SCAN" | python3 -c "import sys, json; signals = json.load(sys.stdin).get('signals', []); print(json.dumps(signals[0])) if signals else print('{}')")

        echo -e "\n${CYAN}Top Signal:${NC}"
        echo "$FIRST_SIGNAL" | python3 -m json.tool

        read -p "Execute this momentum trade? (y/n): " CONFIRM
        if [ "$CONFIRM" != "y" ]; then
            echo -e "${YELLOW}Trade cancelled${NC}"
            exit 0
        fi

        # Execute momentum trade
        echo -e "\n${YELLOW}Executing momentum trade...${NC}"
        RESULT=$(curl -s -X POST "$BACKEND_URL/api/momentum-scalping/execute" \
            -H "Content-Type: application/json" \
            -d "$FIRST_SIGNAL")

        echo "$RESULT" | python3 -m json.tool

        if echo "$RESULT" | grep -q '"order_id"'; then
            echo -e "\n${GREEN}✅ MOMENTUM TRADE EXECUTED!${NC}"
        else
            echo -e "\n${RED}❌ Execution failed${NC}"
            exit 1
        fi
        ;;

    *)
        echo -e "${RED}Invalid choice. Exiting.${NC}"
        exit 1
        ;;
esac

# Post-Execution Monitoring
echo -e "\n${BLUE}========================================${NC}"
echo -e "${BLUE}POSITION MONITORING${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}Your trade is now being monitored!${NC}"
echo ""
echo -e "${YELLOW}Monitoring Features:${NC}"
echo "  - Auto-exit on profit targets"
echo "  - Auto-exit on stop loss"
echo "  - Force close at end of day (for 0DTE)"
echo "  - Real-time P&L tracking"
echo ""
echo -e "${YELLOW}View Position:${NC}"
echo "  Dashboard: https://trade-oracle-lac.vercel.app"
echo "  API: curl $BACKEND_URL/api/execution/positions"
echo ""
echo -e "${YELLOW}Check Exit Conditions:${NC}"
echo "  curl $BACKEND_URL/api/testing/check-exit-conditions"
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}CONGRATULATIONS ON YOUR FIRST TRADE!${NC}"
echo -e "${BLUE}========================================${NC}"
