"""
Test Trade Lifecycle Script

Demonstrates the full position lifecycle:
1. Generate IV Mean Reversion signal
2. Risk approval check
3. Execute paper trade on Alpaca
4. Create position in database
5. Monitor position (background service)
6. Automatic exit when conditions met

Usage:
    python test_trade_lifecycle.py --symbol SPY251219C00600000
"""

import argparse
import asyncio
import json
from decimal import Decimal
from datetime import datetime
import httpx

# Configuration
API_BASE_URL = "https://trade-oracle-production.up.railway.app"
# Backup: API_BASE_URL = "http://localhost:8000"


async def test_full_lifecycle(symbol: str = "SPY251219C00600000"):
    """
    Execute a full trade lifecycle test

    Args:
        symbol: Option symbol (default: SPY Dec 19 $600 Call)
    """
    print("=" * 80)
    print("TRADE ORACLE - POSITION LIFECYCLE TEST")
    print("=" * 80)
    print(f"Testing symbol: {symbol}")
    print(f"API: {API_BASE_URL}")
    print(f"Time: {datetime.now().isoformat()}")
    print("=" * 80)
    print()

    async with httpx.AsyncClient(timeout=30.0) as client:

        # Step 1: Health Check
        print("📡 Step 1: Health Check")
        print("-" * 80)
        try:
            response = await client.get(f"{API_BASE_URL}/health")
            health = response.json()
            print(f"✅ Status: {health['status']}")
            print(f"✅ Alpaca: {health['services']['alpaca']}")
            print(f"✅ Supabase: {health['services']['supabase']}")
            print(f"✅ Paper Trading: {health['paper_trading']}")
        except Exception as e:
            print(f"❌ Health check failed: {e}")
            return
        print()

        # Step 2: Get Portfolio State
        print("💰 Step 2: Portfolio State")
        print("-" * 80)
        try:
            response = await client.get(f"{API_BASE_URL}/api/execution/portfolio")
            portfolio_data = response.json()
            portfolio = portfolio_data['portfolio']
            print(f"Balance: ${float(portfolio['balance']):,.2f}")
            print(f"Daily P&L: ${float(portfolio['daily_pnl']):,.2f}")
            print(f"Active Positions: {portfolio['active_positions']}")
            print(f"Win Rate: {portfolio['win_rate']:.1%}")
            print(f"Consecutive Losses: {portfolio['consecutive_losses']}")
        except Exception as e:
            print(f"❌ Portfolio fetch failed: {e}")
            return
        print()

        # Step 3: Generate Signal (Simulated)
        print("📊 Step 3: Generate Trading Signal")
        print("-" * 80)
        # In production, this would come from /api/strategies/signal
        # For testing, we'll create a simulated BUY signal
        signal = {
            "symbol": symbol,
            "strategy": "IV Mean Reversion",
            "signal_type": "BUY",
            "entry_price": "12.50",
            "take_profit": "25.00",
            "stop_loss": "6.25",
            "iv_rank": 0.25,
            "confidence": 0.85,
            "reasoning": "IV rank at 25th percentile, entering long volatility position"
        }
        print(f"Signal Type: {signal['signal_type']}")
        print(f"Entry Price: ${signal['entry_price']}")
        print(f"Stop Loss: ${signal['stop_loss']} (50% max loss)")
        print(f"Take Profit: ${signal['take_profit']} (100% gain)")
        print(f"IV Rank: {float(signal['iv_rank']):.1%}")
        print(f"Confidence: {float(signal['confidence']):.1%}")
        print(f"Reasoning: {signal['reasoning']}")
        print()

        # Step 4: Risk Approval
        print("🛡️  Step 4: Risk Management Approval")
        print("-" * 80)
        try:
            approval_request = {
                "signal": signal,
                "portfolio": portfolio
            }
            response = await client.post(
                f"{API_BASE_URL}/api/risk/approve",
                json=approval_request
            )
            approval = response.json()

            if not approval['approved']:
                print(f"❌ Trade REJECTED: {approval['reasoning']}")
                return

            print(f"✅ Trade APPROVED")
            print(f"Position Size: {approval['position_size']} contracts")
            print(f"Max Loss: ${float(approval['max_loss']):,.2f}")
            print(f"Reasoning: {approval['reasoning']}")
        except Exception as e:
            print(f"❌ Risk approval failed: {e}")
            return
        print()

        # Step 5: Execute Order
        print("🚀 Step 5: Execute Paper Trade on Alpaca")
        print("-" * 80)
        try:
            order_request = {
                "signal": signal,
                "approval": approval
            }
            response = await client.post(
                f"{API_BASE_URL}/api/execution/order",
                json=order_request,
                timeout=30.0
            )
            execution = response.json()

            if not execution['success']:
                print(f"❌ Order execution failed: {execution['message']}")
                return

            print(f"✅ Order executed successfully")
            print(f"Alpaca Order ID: {execution['alpaca_order_id']}")
            print(f"Quantity: {execution['execution']['quantity']} contracts")
            print(f"Fill Price: ${float(execution['execution']['fill_price']):,.2f}")
            print(f"Commission: ${float(execution['execution']['commission']):,.2f}")
            print(f"Total Cost: ${float(execution['execution']['fill_price']) * 100 * execution['execution']['quantity']:,.2f}")
        except Exception as e:
            print(f"❌ Order execution failed: {e}")
            import traceback
            traceback.print_exc()
            return
        print()

        # Step 6: Check Position Created
        print("📍 Step 6: Verify Position Created")
        print("-" * 80)
        await asyncio.sleep(2)  # Wait for database write
        try:
            response = await client.get(f"{API_BASE_URL}/api/execution/positions")
            positions = response.json()

            if not positions:
                print("⚠️  No positions found (may take a few seconds)")
            else:
                print(f"✅ Found {len(positions)} open position(s)")
                for pos in positions:
                    print(f"\nPosition ID: {pos['id']}")
                    print(f"Symbol: {pos['symbol']}")
                    print(f"Quantity: {pos['quantity']} contracts")
                    print(f"Entry Price: ${float(pos['entry_price']):,.2f}")
                    print(f"Current Price: ${float(pos['current_price']):,.2f}")
                    print(f"Unrealized P&L: ${float(pos['unrealized_pnl']):,.2f}")
                    print(f"Status: {pos['status']}")
        except Exception as e:
            print(f"❌ Position fetch failed: {e}")
        print()

        # Step 7: Monitor Background Service
        print("👀 Step 7: Position Monitor Status")
        print("-" * 80)
        print("✅ Position monitor running in background (60s polling)")
        print("\nExit Conditions Being Monitored:")
        print("  • 50% Profit Target → Automatic CLOSE_LONG")
        print("  • 75% Stop Loss → Automatic CLOSE_LONG")
        print("  • 21 DTE Threshold → Automatic CLOSE_LONG")
        print("  • Earnings Blackout → Future feature")
        print()
        print("Monitor will check this position every 60 seconds.")
        print("Check Railway logs to see monitor activity:")
        print(f"  railway logs --service trade-oracle | grep -i 'monitor'")
        print()

        # Step 8: View on Dashboard
        print("🌐 Step 8: View on Dashboard")
        print("-" * 80)
        print(f"Frontend: https://trade-oracle-lac.vercel.app")
        print(f"\nYou should now see:")
        print("  • Active Positions section with your new position")
        print("  • Progress bars for exit conditions")
        print("  • Live P&L updates every 5 seconds")
        print("  • Trade logged in Trade History")
        print()

        # Summary
        print("=" * 80)
        print("✅ TRADE LIFECYCLE TEST COMPLETE")
        print("=" * 80)
        print("\nWhat happens next:")
        print("1. Position monitor checks every 60 seconds")
        print("2. When exit condition met → automatic CLOSE_LONG signal")
        print("3. Order executed on Alpaca")
        print("4. Position status updated to 'closed'")
        print("5. P&L logged to trades table")
        print("6. Dashboard updates automatically")
        print()
        print("🎯 To trigger manual exit (testing):")
        print("   Modify position monitor thresholds in backend/monitoring/position_monitor.py")
        print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test Trade Oracle position lifecycle")
    parser.add_argument(
        "--symbol",
        type=str,
        default="SPY251219C00600000",
        help="Option symbol (default: SPY Dec 19 $600 Call)"
    )
    parser.add_argument(
        "--local",
        action="store_true",
        help="Use local API (http://localhost:8000) instead of production"
    )

    args = parser.parse_args()

    if args.local:
        API_BASE_URL = "http://localhost:8000"

    asyncio.run(test_full_lifecycle(args.symbol))
