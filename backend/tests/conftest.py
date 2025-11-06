"""
Pytest Configuration and Fixtures

Shared test fixtures for Trade Oracle test suite.
"""

import pytest
import sys
from pathlib import Path
from decimal import Decimal
from datetime import datetime, timezone, timedelta

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def sample_option_tick():
    """Create a sample OptionTick for testing"""
    from models.trading import OptionTick

    return OptionTick(
        symbol="SPY251219C00600000",
        underlying_price=Decimal('600.00'),
        strike=Decimal('600.00'),
        expiration=datetime.now(timezone.utc) + timedelta(days=35),
        bid=Decimal('10.00'),
        ask=Decimal('10.50'),
        delta=Decimal('0.50'),
        gamma=Decimal('0.01'),
        theta=Decimal('-0.05'),
        vega=Decimal('0.15'),
        iv=Decimal('0.30'),
        timestamp=datetime.now(timezone.utc)
    )


@pytest.fixture
def sample_portfolio():
    """Create a sample Portfolio for testing"""
    from models.trading import Portfolio

    return Portfolio(
        balance=Decimal('10000.00'),
        daily_pnl=Decimal('0.00'),
        win_rate=0.55,
        consecutive_losses=0,
        delta=Decimal('0.00'),
        theta=Decimal('0.00'),
        active_positions=0,
        total_trades=10
    )


@pytest.fixture
def sample_signal_buy():
    """Create a sample BUY signal for testing"""
    from models.trading import Signal, SignalType

    return Signal(
        symbol="SPY251219C00600000",
        signal=SignalType.BUY,
        strategy="IV Mean Reversion",
        confidence=0.85,
        entry_price=Decimal('10.00'),
        stop_loss=Decimal('5.00'),
        take_profit=Decimal('20.00'),
        reasoning="Test signal",
        timestamp=datetime.now(timezone.utc)
    )


@pytest.fixture
def sample_signal_sell():
    """Create a sample SELL signal for testing"""
    from models.trading import Signal, SignalType

    return Signal(
        symbol="SPY251219P00590000",
        signal=SignalType.SELL,
        strategy="IV Mean Reversion",
        confidence=0.80,
        entry_price=Decimal('8.00'),
        stop_loss=Decimal('12.00'),
        take_profit=Decimal('4.00'),
        reasoning="Test signal",
        timestamp=datetime.now(timezone.utc)
    )


@pytest.fixture
def sample_position_long():
    """Create a sample long position for testing"""
    from models.trading import Position

    return Position(
        id=1,
        symbol="SPY251219C00600000",
        strategy="IV Mean Reversion",
        position_type="long",
        quantity=10,
        entry_price=Decimal('10.00'),
        entry_trade_id=1,
        current_price=Decimal('12.00'),
        unrealized_pnl=Decimal('2000.00'),
        opened_at=datetime.now(timezone.utc) - timedelta(days=5),
        status="open"
    )


@pytest.fixture
def sample_position_short():
    """Create a sample short position for testing"""
    from models.trading import Position

    return Position(
        id=2,
        symbol="SPY251219P00590000",
        strategy="IV Mean Reversion",
        position_type="short",
        quantity=5,
        entry_price=Decimal('8.00'),
        entry_trade_id=2,
        current_price=Decimal('6.00'),
        unrealized_pnl=Decimal('1000.00'),
        opened_at=datetime.now(timezone.utc) - timedelta(days=3),
        status="open"
    )


@pytest.fixture
def sample_strategy_stats_winning():
    """Create strategy stats with positive expected value"""
    from models.trading import StrategyStats

    return StrategyStats(
        strategy_name="IV Mean Reversion",
        win_rate=0.60,
        avg_win=Decimal('100.00'),
        avg_loss=Decimal('50.00'),
        total_trades=100
    )


@pytest.fixture
def sample_strategy_stats_losing():
    """Create strategy stats with negative expected value"""
    from models.trading import StrategyStats

    return StrategyStats(
        strategy_name="Bad Strategy",
        win_rate=0.40,
        avg_win=Decimal('50.00'),
        avg_loss=Decimal('100.00'),
        total_trades=100
    )
