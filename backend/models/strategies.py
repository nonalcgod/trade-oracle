"""
Strategy Models

Pydantic models for different trading strategies (iron condors, straddles, etc.)
"""

from decimal import Decimal
from datetime import datetime, timezone
from typing import List, Literal
from pydantic import BaseModel, Field, ConfigDict

from models.trading import SignalType


# ============================================================================
# Multi-Leg Order Components
# ============================================================================

class OptionLeg(BaseModel):
    """Single leg of a multi-leg options order"""
    model_config = ConfigDict(from_attributes=True)

    symbol: str
    side: Literal["buy", "sell"]  # Buy to open or sell to open
    quantity: int
    option_type: Literal["call", "put"]
    strike: Decimal
    expiration: datetime
    limit_price: Decimal | None = None  # For individual leg pricing


class MultiLegOrder(BaseModel):
    """Multi-leg options order (spread, condor, butterfly, etc.)"""
    model_config = ConfigDict(from_attributes=True)

    strategy_type: Literal["iron_condor", "call_spread", "put_spread", "straddle", "strangle", "butterfly"]
    legs: List[OptionLeg]
    net_credit: Decimal | None = None  # Expected credit received
    net_debit: Decimal | None = None   # Expected debit paid
    max_profit: Decimal | None = None
    max_loss: Decimal | None = None


# ============================================================================
# Iron Condor Strategy
# ============================================================================

class IronCondorSetup(BaseModel):
    """Configuration for iron condor trade"""
    model_config = ConfigDict(from_attributes=True)

    underlying_symbol: str = Field(..., description="Underlying symbol (SPY, QQQ)")

    # Call spread (short call + long call protection)
    short_call_strike: Decimal
    long_call_strike: Decimal

    # Put spread (short put + long put protection)
    short_put_strike: Decimal
    long_put_strike: Decimal

    # Position sizing
    quantity: int = Field(1, description="Number of iron condors")

    # Pricing
    call_spread_credit: Decimal
    put_spread_credit: Decimal
    total_credit: Decimal

    # Greeks
    net_delta: Decimal | None = None
    net_theta: Decimal | None = None

    # Risk metrics
    max_profit: Decimal  # Total credit received
    max_loss_per_side: Decimal  # Width - credit

    # Expiration
    expiration: datetime
    dte: int  # Days to expiration

    # Entry conditions
    entry_time: datetime
    underlying_price_at_entry: Decimal
    vix_at_entry: Decimal | None = None
    iv_rank_at_entry: Decimal | None = None


class IronCondorExitConditions(BaseModel):
    """Exit rules for iron condor"""
    model_config = ConfigDict(from_attributes=True)
    # Profit targets
    profit_target_pct: Decimal = Field(Decimal("0.50"), description="Close at 50% of max profit")

    # Stop loss
    stop_loss_multiple: Decimal = Field(Decimal("2.0"), description="Close if loss is 2x credit")

    # Time-based
    exit_time: str = Field("15:50", description="Time to close position (HH:MM)")

    # Breach detection
    call_breach_buffer: Decimal = Field(Decimal("0.02"), description="Close if price within 2% of short call")
    put_breach_buffer: Decimal = Field(Decimal("0.02"), description="Close if price within 2% of short put")

    # Manual override
    force_close: bool = False


class IronCondorSignal(BaseModel):
    """Signal to enter/exit iron condor"""
    model_config = ConfigDict(from_attributes=True)

    action: Literal["open", "close", "adjust"]
    setup: IronCondorSetup | None = None
    exit_reason: str | None = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ============================================================================
# Earnings Strategy
# ============================================================================

class EarningsEvent(BaseModel):
    """Earnings event data"""
    model_config = ConfigDict(from_attributes=True)

    symbol: str
    earnings_date: datetime
    estimate_eps: Decimal | None = None
    actual_eps: Decimal | None = None
    surprise_pct: Decimal | None = None

    # Historical data
    avg_move_pct: Decimal | None = None  # Historical average move
    implied_move_pct: Decimal | None = None  # Current implied move

    # Volatility data
    iv_rank: Decimal | None = None
    iv_percentile: Decimal | None = None

    # Timing
    before_market: bool = True  # True if before market open, False if after close


class StraddleSetup(BaseModel):
    """ATM straddle configuration"""
    model_config = ConfigDict(from_attributes=True)

    symbol: str
    strike: Decimal  # ATM strike
    expiration: datetime

    # Pricing
    call_price: Decimal
    put_price: Decimal
    total_cost: Decimal

    # Break-even points
    upper_breakeven: Decimal  # strike + total_cost
    lower_breakeven: Decimal  # strike - total_cost

    # Entry conditions
    entry_time: datetime
    underlying_price: Decimal
    iv_rank: Decimal

    # Earnings context
    earnings_event: EarningsEvent

    # Position sizing
    quantity: int = 1


class EarningsStraddleSignal(BaseModel):
    """Signal for earnings straddle trade"""
    model_config = ConfigDict(from_attributes=True)

    action: Literal["open_long_straddle", "open_short_iron_condor", "close"]
    setup: StraddleSetup | None = None
    timing: Literal["before_earnings", "after_earnings"]
    reasoning: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ============================================================================
# Momentum Strategy
# ============================================================================

class MomentumIndicators(BaseModel):
    """Technical indicators for momentum strategy"""
    model_config = ConfigDict(from_attributes=True)

    rsi: Decimal
    macd: Decimal
    macd_signal: Decimal
    macd_histogram: Decimal

    # Moving averages
    sma_20: Decimal | None = None
    sma_50: Decimal | None = None
    ema_12: Decimal | None = None
    ema_26: Decimal | None = None

    # Volatility
    atr: Decimal | None = None
    bollinger_upper: Decimal | None = None
    bollinger_lower: Decimal | None = None

    # Trend strength
    adx: Decimal | None = None


class MomentumSignal(BaseModel):
    """Signal for momentum-based option trade"""
    model_config = ConfigDict(from_attributes=True)

    direction: Literal["bullish", "bearish", "neutral"]
    confidence: Decimal = Field(..., ge=0, le=1)

    # Recommended position
    position_type: Literal["long_call", "long_put", "call_spread", "put_spread"]

    # Entry details
    symbol: str
    underlying_price: Decimal
    indicators: MomentumIndicators

    # Option details
    suggested_strike: Decimal
    suggested_expiration: datetime
    suggested_dte: int

    # Exit rules
    take_profit_pct: Decimal = Decimal("0.50")
    stop_loss_pct: Decimal = Decimal("0.25")

    # Timing
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    reasoning: str


# ============================================================================
# Strategy Performance Tracking
# ============================================================================

class StrategyPerformance(BaseModel):
    """Performance metrics for a strategy"""
    model_config = ConfigDict(from_attributes=True)

    strategy_name: str

    # Trade statistics
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: Decimal

    # P&L
    total_pnl: Decimal
    avg_win: Decimal
    avg_loss: Decimal
    profit_factor: Decimal  # avg_win / avg_loss

    # Risk metrics
    max_drawdown: Decimal
    sharpe_ratio: Decimal | None = None
    sortino_ratio: Decimal | None = None

    # Time period
    start_date: datetime
    end_date: datetime
    days_active: int

    # Capital efficiency
    avg_position_size: Decimal
    return_on_capital: Decimal


class StrategyComparison(BaseModel):
    """Compare multiple strategies"""
    model_config = ConfigDict(from_attributes=True)

    strategies: List[StrategyPerformance]

    # Best performers
    best_win_rate: str  # Strategy name
    best_profit_factor: str
    best_sharpe: str
    lowest_drawdown: str

    # Portfolio level
    combined_win_rate: Decimal
    combined_sharpe: Decimal
    correlation_matrix: dict | None = None  # Strategy correlation
