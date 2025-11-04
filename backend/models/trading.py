from pydantic import BaseModel, Field
from decimal import Decimal
from datetime import datetime
from enum import Enum


class SignalType(str, Enum):
    BUY = "buy"
    SELL = "sell"


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


class Signal(BaseModel):
    symbol: str
    signal: SignalType
    strategy: str
    confidence: float = Field(ge=0.0, le=1.0)
    entry_price: Decimal
    stop_loss: Decimal
    take_profit: Decimal
    reasoning: str


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
