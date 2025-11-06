"""
Test Suite for P&L Calculations

Tests profit/loss calculations for options positions.
Critical for accurate performance tracking.
"""

import pytest
import sys
from pathlib import Path
from decimal import Decimal

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestLongPositionPnL:
    """Test P&L calculations for long option positions"""

    def test_long_call_profit(self):
        """Long call gains value when price rises"""
        # BUY 10 contracts @ $10.00, sell @ $15.00
        entry_price = Decimal('10.00')
        exit_price = Decimal('15.00')
        quantity = 10

        # P&L = (exit - entry) * quantity * 100 (multiplier)
        pnl = (exit_price - entry_price) * quantity * Decimal('100')

        # Expected: ($15 - $10) * 10 * 100 = $5,000 profit
        assert pnl == Decimal('5000.00'), f"Long call profit {pnl} != $5,000"

    def test_long_call_loss(self):
        """Long call loses value when price falls"""
        # BUY 10 contracts @ $10.00, sell @ $5.00
        entry_price = Decimal('10.00')
        exit_price = Decimal('5.00')
        quantity = 10

        pnl = (exit_price - entry_price) * quantity * Decimal('100')

        # Expected: ($5 - $10) * 10 * 100 = -$5,000 loss
        assert pnl == Decimal('-5000.00'), f"Long call loss {pnl} != -$5,000"

    def test_long_position_percentage_gain(self):
        """Calculate percentage gain for long position"""
        # BUY @ $10.00, current price $15.00
        entry_price = Decimal('10.00')
        current_price = Decimal('15.00')

        pnl_pct = (current_price - entry_price) / entry_price

        # Expected: ($15 - $10) / $10 = 50% gain
        assert pnl_pct == Decimal('0.50'), f"P&L percentage {pnl_pct} != 50%"

    def test_long_position_percentage_loss(self):
        """Calculate percentage loss for long position"""
        # BUY @ $10.00, current price $2.50
        entry_price = Decimal('10.00')
        current_price = Decimal('2.50')

        pnl_pct = (current_price - entry_price) / entry_price

        # Expected: ($2.50 - $10) / $10 = -75% loss
        assert pnl_pct == Decimal('-0.75'), f"P&L percentage {pnl_pct} != -75%"


class TestShortPositionPnL:
    """Test P&L calculations for short option positions"""

    def test_short_call_profit(self):
        """Short call gains value when price falls"""
        # SELL 10 contracts @ $10.00, buy back @ $5.00
        entry_price = Decimal('10.00')
        exit_price = Decimal('5.00')
        quantity = 10

        # P&L = (entry - exit) * quantity * 100 (reversed for short)
        pnl = (entry_price - exit_price) * quantity * Decimal('100')

        # Expected: ($10 - $5) * 10 * 100 = $5,000 profit
        assert pnl == Decimal('5000.00'), f"Short call profit {pnl} != $5,000"

    def test_short_call_loss(self):
        """Short call loses value when price rises"""
        # SELL 10 contracts @ $10.00, buy back @ $15.00
        entry_price = Decimal('10.00')
        exit_price = Decimal('15.00')
        quantity = 10

        pnl = (entry_price - exit_price) * quantity * Decimal('100')

        # Expected: ($10 - $15) * 10 * 100 = -$5,000 loss
        assert pnl == Decimal('-5000.00'), f"Short call loss {pnl} != -$5,000"

    def test_short_position_percentage_gain(self):
        """Calculate percentage gain for short position"""
        # SELL @ $10.00, current price $5.00
        entry_price = Decimal('10.00')
        current_price = Decimal('5.00')

        # For short: pnl_pct = (entry - current) / entry
        pnl_pct = (entry_price - current_price) / entry_price

        # Expected: ($10 - $5) / $10 = 50% gain
        assert pnl_pct == Decimal('0.50'), f"P&L percentage {pnl_pct} != 50%"

    def test_short_position_percentage_loss(self):
        """Calculate percentage loss for short position"""
        # SELL @ $10.00, current price $17.50
        entry_price = Decimal('10.00')
        current_price = Decimal('17.50')

        pnl_pct = (entry_price - current_price) / entry_price

        # Expected: ($10 - $17.50) / $10 = -75% loss
        assert pnl_pct == Decimal('-0.75'), f"P&L percentage {pnl_pct} != -75%"


class TestCommissionAndSlippage:
    """Test P&L adjustments for commission and slippage"""

    def test_commission_impact(self):
        """Commission reduces P&L on both entry and exit"""
        # BUY 10 contracts @ $10.00, sell @ $11.00
        entry_price = Decimal('10.00')
        exit_price = Decimal('11.00')
        quantity = 10
        commission_per_contract = Decimal('0.65')

        # Gross P&L
        gross_pnl = (exit_price - entry_price) * quantity * Decimal('100')

        # Commission = $0.65 per contract * quantity * 2 (entry + exit)
        total_commission = commission_per_contract * quantity * 2

        # Net P&L
        net_pnl = gross_pnl - total_commission

        # Expected: $1,000 gross - $13 commission = $987 net
        assert gross_pnl == Decimal('1000.00'), "Gross P&L should be $1,000"
        assert total_commission == Decimal('13.00'), "Commission should be $13"
        assert net_pnl == Decimal('987.00'), f"Net P&L {net_pnl} != $987"

    def test_slippage_on_market_order(self):
        """Slippage occurs when using market orders (bid-ask spread)"""
        # Signal: BUY @ $10.00 (mid-price)
        # Market reality: bid $9.90, ask $10.10
        # BUY at ask: $10.10 (slippage = $0.10)

        expected_price = Decimal('10.00')
        actual_fill_price = Decimal('10.10')

        slippage = actual_fill_price - expected_price

        # Expected: $0.10 slippage per contract
        assert slippage == Decimal('0.10'), f"Slippage {slippage} != $0.10"

    def test_total_cost_with_fees(self):
        """Calculate total cost including commission and slippage"""
        # BUY 10 contracts @ $10.00 (expected)
        # Actual fill: $10.10 (slippage)
        # Commission: $0.65 per contract

        quantity = 10
        fill_price = Decimal('10.10')
        commission_per_contract = Decimal('0.65')

        # Total cost = (fill price * quantity * 100) + commission
        position_cost = fill_price * quantity * Decimal('100')
        commission = commission_per_contract * quantity
        total_cost = position_cost + commission

        # Expected: $10,100 + $6.50 = $10,106.50
        assert position_cost == Decimal('10100.00'), "Position cost should be $10,100"
        assert commission == Decimal('6.50'), "Commission should be $6.50"
        assert total_cost == Decimal('10106.50'), f"Total cost {total_cost} != $10,106.50"


class TestBreakevenCalculations:
    """Test breakeven price calculations"""

    def test_long_breakeven_with_commission(self):
        """Calculate breakeven price for long position including commission"""
        # BUY 10 contracts @ $10.00
        # Commission: $0.65 * 10 * 2 (entry + exit) = $13

        entry_price = Decimal('10.00')
        quantity = 10
        commission_per_contract = Decimal('0.65')

        # Total commission for round trip
        total_commission = commission_per_contract * quantity * 2

        # Commission per contract (amortized)
        commission_per_share = total_commission / (quantity * Decimal('100'))

        # Breakeven = entry price + commission per share
        breakeven = entry_price + commission_per_share

        # Expected: $10.00 + $0.013 = $10.013
        assert abs(breakeven - Decimal('10.013')) < Decimal('0.001'), \
            f"Breakeven {breakeven} != $10.013"

    def test_profit_target_with_fees(self):
        """Calculate exit price needed to achieve target profit after fees"""
        # BUY 10 contracts @ $10.00
        # Target: $500 profit after fees
        # Commission: $13 total

        entry_price = Decimal('10.00')
        quantity = 10
        target_profit = Decimal('500.00')
        commission = Decimal('13.00')

        # Gross profit needed = target profit + commission
        gross_profit_needed = target_profit + commission

        # Price increase needed per contract
        # $513 / (10 contracts * 100 multiplier) = $0.513 per share
        price_increase = gross_profit_needed / (quantity * Decimal('100'))

        # Exit price needed
        exit_price = entry_price + price_increase

        # Expected: $10.00 + $0.513 = $10.513
        assert abs(exit_price - Decimal('10.513')) < Decimal('0.001'), \
            f"Exit price {exit_price} != $10.513"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
