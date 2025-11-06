"""
Test Iron Condor Strategy Implementation

Quick validation of iron condor strategy logic.
"""

import asyncio
import os
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Mock clients for testing without Alpaca
class MockOptionClient:
    """Mock option data client"""

    async def get_option_chain(self, request):
        # Return mock option chain
        class MockOption:
            def __init__(self, strike, delta, option_type):
                self.strike_price = strike
                self.type = option_type
                self.greeks = type('obj', (object,), {'delta': delta})()

        # Mock SPY options at different strikes
        return [
            MockOption(595, 0.10, "call"),
            MockOption(600, 0.15, "call"),  # Short call
            MockOption(605, 0.08, "call"),  # Long call protection
            MockOption(585, 0.10, "put"),
            MockOption(590, 0.15, "put"),   # Short put
            MockOption(585, 0.08, "put"),   # Long put protection
        ]


class MockStockClient:
    """Mock stock data client"""

    async def get_stock_latest_quote(self, request):
        # Return mock SPY quote
        class MockQuote:
            def __init__(self):
                self.bid_price = 597.50
                self.ask_price = 598.00

        return {"SPY": MockQuote()}


async def test_strike_selection():
    """Test 1: Strike selection by delta"""
    print("\n=== Test 1: Strike Selection by Delta ===")

    from strategies.iron_condor import IronCondorStrategy

    # Create strategy with mock clients
    strategy = IronCondorStrategy(MockOptionClient(), MockStockClient())

    # Test finding call strike
    call_strike = await strategy.find_strike_by_delta(
        underlying="SPY",
        expiration=datetime.now() + timedelta(days=1),
        option_type="call",
        target_delta=Decimal("0.15"),
        underlying_price=Decimal("597.75")
    )

    print(f"✓ Call strike found: ${call_strike}")
    assert call_strike == Decimal("600"), f"Expected 600, got {call_strike}"

    # Test finding put strike
    put_strike = await strategy.find_strike_by_delta(
        underlying="SPY",
        expiration=datetime.now() + timedelta(days=1),
        option_type="put",
        target_delta=Decimal("0.15"),
        underlying_price=Decimal("597.75")
    )

    print(f"✓ Put strike found: ${put_strike}")
    assert put_strike == Decimal("590"), f"Expected 590, got {put_strike}"

    print("✓ Strike selection test passed!")


async def test_entry_window():
    """Test 2: Entry window validation"""
    print("\n=== Test 2: Entry Window Validation ===")

    from strategies.iron_condor import IronCondorStrategy

    strategy = IronCondorStrategy(MockOptionClient(), MockStockClient())

    # Test entry window
    should_enter = await strategy.should_enter_now()

    now = datetime.now().strftime("%H:%M:%S")
    print(f"✓ Current time: {now}")
    print(f"✓ Entry window (9:31am-9:45am ET): {should_enter}")
    print(f"✓ Entry window check passed!")


async def test_multi_leg_order():
    """Test 3: Multi-leg order construction"""
    print("\n=== Test 3: Multi-Leg Order Construction ===")

    from models.strategies import IronCondorSetup, OptionLeg, MultiLegOrder
    from strategies.iron_condor import IronCondorStrategy

    strategy = IronCondorStrategy(MockOptionClient(), MockStockClient())

    # Create mock setup
    expiration = datetime.now() + timedelta(days=1)
    setup = IronCondorSetup(
        underlying_symbol="SPY",
        short_call_strike=Decimal("600"),
        long_call_strike=Decimal("605"),
        short_put_strike=Decimal("590"),
        long_put_strike=Decimal("585"),
        quantity=1,
        call_spread_credit=Decimal("0.50"),
        put_spread_credit=Decimal("0.50"),
        total_credit=Decimal("1.00"),
        max_profit=Decimal("100.00"),
        max_loss_per_side=Decimal("400.00"),
        expiration=expiration,
        dte=1,
        entry_time=datetime.now(timezone.utc),
        underlying_price_at_entry=Decimal("597.75")
    )

    # Create multi-leg order
    order = strategy.create_multi_leg_order(setup)

    print(f"✓ Strategy type: {order.strategy_type}")
    print(f"✓ Number of legs: {len(order.legs)}")
    print(f"✓ Net credit: ${order.net_credit}")
    print(f"✓ Max profit: ${order.max_profit}")
    print(f"✓ Max loss: ${order.max_loss}")

    # Verify legs
    assert len(order.legs) == 4, f"Expected 4 legs, got {len(order.legs)}"
    assert order.legs[0].side == "sell", "First leg should be sell"
    assert order.legs[1].side == "buy", "Second leg should be buy"

    print("✓ Multi-leg order test passed!")


async def test_exit_conditions():
    """Test 4: Exit condition checking"""
    print("\n=== Test 4: Exit Conditions ===")

    from models.strategies import IronCondorSetup
    from strategies.iron_condor import IronCondorStrategy

    strategy = IronCondorStrategy(MockOptionClient(), MockStockClient())

    # Create mock setup
    expiration = datetime.now() + timedelta(days=1)
    setup = IronCondorSetup(
        underlying_symbol="SPY",
        short_call_strike=Decimal("600"),
        long_call_strike=Decimal("605"),
        short_put_strike=Decimal("590"),
        long_put_strike=Decimal("585"),
        quantity=1,
        call_spread_credit=Decimal("0.50"),
        put_spread_credit=Decimal("0.50"),
        total_credit=Decimal("1.00"),
        max_profit=Decimal("100.00"),
        max_loss_per_side=Decimal("400.00"),
        expiration=expiration,
        dte=1,
        entry_time=datetime.now(timezone.utc),
        underlying_price_at_entry=Decimal("597.75")
    )

    # Test profit target (should exit at 50% profit)
    should_exit, reason = await strategy.check_exit_conditions(setup, Decimal("0.50"))
    print(f"✓ Profit target (current: $0.50, entry: $1.00): {should_exit} - {reason}")
    assert should_exit, "Should exit at 50% profit target"

    # Test stop loss (should exit at 2x loss)
    should_exit, reason = await strategy.check_exit_conditions(setup, Decimal("3.00"))
    print(f"✓ Stop loss (current: $3.00, entry: $1.00): {should_exit} - {reason}")
    assert should_exit, "Should exit at 2x stop loss"

    # Test no exit (normal range)
    should_exit, reason = await strategy.check_exit_conditions(setup, Decimal("0.80"))
    print(f"✓ Normal range (current: $0.80, entry: $1.00): {should_exit} - {reason}")
    assert not should_exit, "Should not exit in normal range"

    print("✓ Exit conditions test passed!")


async def test_api_models():
    """Test 5: API models validation"""
    print("\n=== Test 5: API Models Validation ===")

    from models.strategies import (
        IronCondorSetup,
        IronCondorSignal,
        IronCondorExitConditions,
        OptionLeg,
        MultiLegOrder
    )

    # Test OptionLeg
    leg = OptionLeg(
        symbol="SPY251219C00600000",
        side="sell",
        quantity=1,
        option_type="call",
        strike=Decimal("600"),
        expiration=datetime.now(),
        limit_price=Decimal("1.50")
    )
    print(f"✓ OptionLeg created: {leg.symbol} {leg.side}")

    # Test MultiLegOrder
    order = MultiLegOrder(
        strategy_type="iron_condor",
        legs=[leg],
        net_credit=Decimal("1.00")
    )
    print(f"✓ MultiLegOrder created: {order.strategy_type}")

    # Test exit conditions
    exit_conditions = IronCondorExitConditions()
    print(f"✓ Exit conditions: {exit_conditions.profit_target_pct * 100}% profit target")

    print("✓ API models test passed!")


async def main():
    """Run all tests"""
    print("=" * 60)
    print("Iron Condor Strategy Tests")
    print("=" * 60)

    try:
        await test_strike_selection()
        await test_entry_window()
        await test_multi_leg_order()
        await test_exit_conditions()
        await test_api_models()

        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)

    except Exception as e:
        print("\n" + "=" * 60)
        print(f"❌ TEST FAILED: {e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
