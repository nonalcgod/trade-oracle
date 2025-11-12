#!/bin/bash
# Real-Time Position Monitoring
# Run this after executing a trade to watch it live
#
# Usage: ./monitor_position.sh [position_id]
# If no position_id provided, monitors all open positions

BACKEND_URL="https://trade-oracle-production.up.railway.app"
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

POSITION_ID=$1
REFRESH_INTERVAL=5  # seconds

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}POSITION MONITOR - LIVE${NC}"
echo -e "${BLUE}========================================${NC}"

while true; do
    clear
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}POSITION MONITOR - $(date '+%H:%M:%S')${NC}"
    echo -e "${BLUE}========================================${NC}"

    # Get all positions
    POSITIONS=$(curl -s "$BACKEND_URL/api/execution/positions")

    # Filter open positions
    OPEN_POSITIONS=$(echo "$POSITIONS" | python3 -c "
import sys, json
positions = json.load(sys.stdin)
open_pos = [p for p in positions if p.get('status') == 'open']
print(len(open_pos))
")

    if [ "$OPEN_POSITIONS" -eq 0 ]; then
        echo -e "${YELLOW}No open positions${NC}"
        echo ""
        echo -e "${GREEN}All positions closed!${NC}"
        break
    fi

    echo -e "${GREEN}Open Positions: $OPEN_POSITIONS${NC}"
    echo ""

    # Display each position
    echo "$POSITIONS" | python3 - <<'PYTHON'
import sys
import json
from datetime import datetime

positions = json.load(sys.stdin)
open_positions = [p for p in positions if p.get('status') == 'open']

GREEN = '\033[0;32m'
RED = '\033[0;31m'
YELLOW = '\033[1;33m'
CYAN = '\033[0;36m'
NC = '\033[0m'

for i, pos in enumerate(open_positions, 1):
    print(f"{CYAN}Position #{i}{NC}")
    print(f"  ID: {pos.get('id', 'N/A')}")
    print(f"  Symbol: {pos.get('symbol', 'N/A')}")
    print(f"  Strategy: {pos.get('strategy', 'N/A')}")
    print(f"  Type: {pos.get('position_type', 'N/A')}")

    # P&L
    unrealized_pnl = pos.get('unrealized_pnl', 0)
    if unrealized_pnl is not None:
        unrealized_pnl = float(unrealized_pnl)
        pnl_color = GREEN if unrealized_pnl >= 0 else RED
        pnl_sign = '+' if unrealized_pnl >= 0 else ''
        print(f"  P&L: {pnl_color}{pnl_sign}${unrealized_pnl:.2f}{NC}")

    # Entry/Current Price
    entry_price = pos.get('entry_price', 0)
    current_price = pos.get('current_price', 0)
    if entry_price and current_price:
        pct_change = ((float(current_price) - float(entry_price)) / float(entry_price)) * 100
        pct_color = GREEN if pct_change >= 0 else RED
        pct_sign = '+' if pct_change >= 0 else ''
        print(f"  Entry: ${float(entry_price):.2f}")
        print(f"  Current: ${float(current_price):.2f} ({pct_color}{pct_sign}{pct_change:.2f}%{NC})")

    # Targets
    take_profit = pos.get('take_profit_price')
    stop_loss = pos.get('stop_loss_price')
    if take_profit:
        print(f"  {GREEN}Take Profit: ${float(take_profit):.2f}{NC}")
    if stop_loss:
        print(f"  {RED}Stop Loss: ${float(stop_loss):.2f}{NC}")

    # Time
    opened_at = pos.get('opened_at', '')
    if opened_at:
        print(f"  Opened: {opened_at}")

    print()

PYTHON

    # Check exit conditions
    echo -e "${YELLOW}Checking exit conditions...${NC}"
    EXIT_CHECK=$(curl -s "$BACKEND_URL/api/testing/check-exit-conditions")

    # Parse exit check results
    echo "$EXIT_CHECK" | python3 - <<'PYTHON'
import sys
import json

try:
    data = json.load(sys.stdin)
    results = data.get('results', [])

    GREEN = '\033[0;32m'
    RED = '\033[0;31m'
    YELLOW = '\033[1;33m'
    NC = '\033[0m'

    for result in results:
        pos_id = result.get('position_id', 'N/A')
        should_exit = result.get('should_exit', False)
        reason = result.get('reason', '')

        if should_exit:
            print(f"{RED}⚠️  Position {pos_id}: Should EXIT - {reason}{NC}")
        else:
            print(f"{GREEN}✓ Position {pos_id}: Holding - {reason}{NC}")

except Exception as e:
    print(f"{YELLOW}Could not parse exit conditions{NC}")
PYTHON

    echo ""
    echo -e "${BLUE}Auto-refresh in ${REFRESH_INTERVAL}s (Ctrl+C to stop)${NC}"
    sleep $REFRESH_INTERVAL
done

echo -e "\n${BLUE}========================================${NC}"
echo -e "${GREEN}Monitoring complete${NC}"
echo -e "${BLUE}========================================${NC}"
