from pydantic import BaseModel, Field, ConfigDict, field_validator
from decimal import Decimal
from datetime import datetime, timezone
from typing import Any
from enum import Enum


# ============================================================================
# Enums for Type Safety
# ============================================================================

class SignalType(str, Enum):
    """Trading signal types"""
    BUY = "buy"              # Buy to open (long position)
    SELL = "sell"            # Sell to open (short position)
    CLOSE_LONG = "close_long"      # Sell to close long position
    CLOSE_SHORT = "close_short"    # Buy to close short position


class PositionType(str, Enum):
    """Position/strategy types"""
    LONG = "long"
    SHORT = "short"
    SPREAD = "spread"
    IRON_CONDOR = "iron_condor"
    MOMENTUM_SCALPING = "momentum_scalping"
    OPENING_RANGE_BREAKOUT = "opening_range_breakout"
    STRADDLE = "straddle"
    STRANGLE = "strangle"
    BUTTERFLY = "butterfly"
    CALENDAR = "calendar"


class PositionStatus(str, Enum):
    """Position lifecycle status"""
    OPEN = "open"
    CLOSED = "closed"


class ExitReason(str, Enum):
    """Reasons for closing a position"""
    PROFIT_TARGET = "profit_target"
    STOP_LOSS = "stop_loss"
    TIME_DECAY = "time_decay"
    EARNINGS_BLACKOUT = "earnings_blackout"
    BREACH = "breach"
    MANUAL = "manual"
    FORCE_CLOSE = "force_close"


# ============================================================================
# Market Data Models
# ============================================================================

class OptionTick(BaseModel):
    """Real-time option market data with Greeks"""
    model_config = ConfigDict(from_attributes=True)

    symbol: str
    underlying_price: Decimal = Field(gt=0, description="Underlying price must be positive")
    strike: Decimal = Field(gt=0, description="Strike price must be positive")
    expiration: datetime
    bid: Decimal = Field(ge=0, description="Bid cannot be negative")
    ask: Decimal = Field(ge=0, description="Ask cannot be negative")
    delta: Decimal = Field(ge=-1, le=1, description="Delta range: -1 to 1")
    gamma: Decimal = Field(ge=0, description="Gamma always positive")
    theta: Decimal
    vega: Decimal = Field(ge=0, description="Vega always positive")
    iv: Decimal = Field(ge=0, le=2, description="IV range: 0-200%")
    timestamp: datetime

    @field_validator('ask')
    @classmethod
    def ask_must_exceed_bid(cls, v: Decimal, info) -> Decimal:
        """Validate bid/ask spread is valid"""
        if 'bid' in info.data and v < info.data['bid']:
            raise ValueError(f'ask ({v}) must be >= bid ({info.data["bid"]})')
        return v

    @property
    def mid_price(self) -> Decimal:
        """Calculate mid-price between bid and ask"""
        return (self.bid + self.ask) / 2

    @property
    def dte(self) -> int:
        """Calculate days to expiration from current timestamp"""
        return (self.expiration - self.timestamp).days


# ============================================================================
# Trading Signal Models
# ============================================================================

class Signal(BaseModel):
    """Trading signal with entry/exit levels"""
    model_config = ConfigDict(from_attributes=True)

    symbol: str
    signal: SignalType
    strategy: str
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence: 0-100%")
    entry_price: Decimal
    stop_loss: Decimal
    take_profit: Decimal
    reasoning: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ============================================================================
# Risk Management Models
# ============================================================================

class RiskApproval(BaseModel):
    """Risk management approval result"""
    model_config = ConfigDict(from_attributes=True)

    approved: bool
    position_size: int = 0
    max_loss: Decimal = Decimal('0')
    reasoning: str


# ============================================================================
# Portfolio Models
# ============================================================================

class Portfolio(BaseModel):
    """Portfolio state with Greeks and metrics"""
    model_config = ConfigDict(from_attributes=True)

    balance: Decimal
    daily_pnl: Decimal
    win_rate: float = Field(ge=0.0, le=1.0)
    consecutive_losses: int = Field(ge=0)
    delta: Decimal
    theta: Decimal
    active_positions: int = Field(ge=0)
    total_trades: int = Field(ge=0, default=0)


class StrategyStats(BaseModel):
    """Historical performance statistics for a trading strategy"""
    model_config = ConfigDict(from_attributes=True)

    strategy_name: str
    win_rate: float = Field(ge=0.0, le=1.0, default=0.0)
    avg_win: Decimal = Decimal('0')
    avg_loss: Decimal = Decimal('0')
    total_trades: int = Field(ge=0, default=0)


# ============================================================================
# Execution Models
# ============================================================================

class Execution(BaseModel):
    """Trade execution record with P&L tracking"""
    model_config = ConfigDict(from_attributes=True)

    symbol: str
    quantity: int
    entry_price: Decimal
    exit_price: Decimal | None = None
    pnl: Decimal | None = None
    commission: Decimal = Decimal('0')
    slippage: Decimal = Decimal('0')
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ============================================================================
# Position Models
# ============================================================================

class Position(BaseModel):
    """Open or closed position with full lifecycle tracking"""
    model_config = ConfigDict(from_attributes=True)

    # Core position fields
    id: int | None = None
    symbol: str
    strategy: str
    position_type: PositionType
    quantity: int
    entry_price: Decimal
    entry_trade_id: int | None = None
    current_price: Decimal | None = None
    unrealized_pnl: Decimal | None = None
    opened_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    closed_at: datetime | None = None
    exit_trade_id: int | None = None
    exit_reason: ExitReason | None = None
    status: PositionStatus = PositionStatus.OPEN

    # Multi-leg position fields (for iron condors, spreads, etc.)
    legs: list[dict[str, Any]] | None = None  # JSONB array of leg data
    net_credit: Decimal | None = None  # Net credit received or debit paid
    max_loss: Decimal | None = None  # Maximum loss per position
    spread_width: Decimal | None = None  # Width of spread in dollars
