from pydantic import BaseModel, Field
from decimal import Decimal
from datetime import datetime
from typing import Optional
from enum import Enum


class SignalType(str, Enum):
    BUY = "buy"              # Buy to open (long position)
    SELL = "sell"            # Sell to open (short position)
    CLOSE_LONG = "close_long"      # Sell to close long position
    CLOSE_SHORT = "close_short"    # Buy to close short position


class OptionTick(BaseModel):
    symbol: str
    underlying_price: Decimal
    strike: Decimal
    expiration: datetime
    bid: Decimal
    ask: Decimal
    delta: Decimal
    gamma: Decimal
    theta: Decimal
    vega: Decimal
    iv: Decimal
    timestamp: datetime

    @property
    def mid_price(self) -> Decimal:
        return (self.bid + self.ask) / 2

    @property
    def dte(self) -> int:
        """Days to expiration"""
        return (self.expiration - self.timestamp).days


class Signal(BaseModel):
    symbol: str
    signal: SignalType
    strategy: str
    confidence: float = Field(ge=0.0, le=1.0)
    entry_price: Decimal
    stop_loss: Decimal
    take_profit: Decimal
    reasoning: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class RiskApproval(BaseModel):
    approved: bool
    position_size: int = 0
    max_loss: Decimal = Decimal('0')
    reasoning: str


class Portfolio(BaseModel):
    balance: Decimal
    daily_pnl: Decimal
    win_rate: float
    consecutive_losses: int
    delta: Decimal
    theta: Decimal
    active_positions: int
    total_trades: int = 0


class StrategyStats(BaseModel):
    """Historical performance statistics for a trading strategy"""
    strategy_name: str
    win_rate: float = 0.0
    avg_win: Decimal = Decimal('0')
    avg_loss: Decimal = Decimal('0')
    total_trades: int = 0


class Execution(BaseModel):
    """Trade execution record with P&L tracking"""
    symbol: str
    quantity: int
    entry_price: Decimal
    exit_price: Optional[Decimal] = None
    pnl: Optional[Decimal] = None
    commission: Decimal = Decimal('0')
    slippage: Decimal = Decimal('0')
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class Position(BaseModel):
    """Open or closed position with full lifecycle tracking"""
    id: Optional[int] = None
    symbol: str
    strategy: str
    position_type: str  # 'long' or 'short'
    quantity: int
    entry_price: Decimal
    entry_trade_id: Optional[int] = None
    current_price: Optional[Decimal] = None
    unrealized_pnl: Optional[Decimal] = None
    opened_at: datetime = Field(default_factory=datetime.utcnow)
    closed_at: Optional[datetime] = None
    exit_trade_id: Optional[int] = None
    exit_reason: Optional[str] = None
    status: str = "open"  # 'open' or 'closed'
