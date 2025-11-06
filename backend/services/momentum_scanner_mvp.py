"""
0DTE Momentum Scalping Scanner MVP.

Real-time scanner for 6-condition momentum setups.
- EMA 9/21 crossover
- RSI(14) confirmation
- 2x volume spike
- VWAP breakout
- Relative strength (optional for MVP)
- Entry window (9:31-11:30am ET only)
"""

from datetime import datetime, timezone, time
from typing import List, Optional, Dict, Any
from decimal import Decimal
import os
import structlog

from alpaca.data.timeframe import TimeFrame
from pydantic import BaseModel, Field

from backend.utils.indicators import (
    calculate_ema,
    calculate_rsi,
    calculate_vwap,
    calculate_relative_volume,
    detect_ema_crossover,
    validate_6_conditions,
)

logger = structlog.get_logger()

# Eastern Time Zone for entry window checks
EASTERN_TZ = timezone(datetime.now(timezone.utc).astimezone().tzinfo)


class MomentumSignal(BaseModel):
    """Momentum scalping signal."""

    signal_id: str
    symbol: str
    signal_type: str  # "BUY" or "SELL"
    option_symbol: Optional[str] = None
    confidence: float = Field(ge=0, le=1)

    # Technical indicators
    ema_9: float
    ema_21: float
    rsi_14: float
    vwap: float
    relative_volume: float

    # Entry/Exit levels
    entry_price: Optional[float] = None
    target_1: Optional[float] = None  # 25% profit
    target_2: Optional[float] = None  # 50% profit
    stop_loss: Optional[float] = None  # 50% loss

    # Metadata
    created_at: str
    reasoning: str = ""

    class Config:
        from_attributes = True


class MomentumScanner:
    """
    Scanner for 0DTE momentum scalping opportunities.

    Validates all 6 conditions:
    1. EMA(9) crosses EMA(21)
    2. RSI(14) confirmation (>30 for long, <70 for short)
    3. Volume spike (≥2x average)
    4. VWAP breakout
    5. Relative strength (SPY vs QQQ or sectors)
    6. Time window (9:31-11:30am ET)
    """

    def __init__(self, symbols: List[str] = None):
        """
        Initialize scanner.

        Args:
            symbols: List of symbols to monitor (default: SPY, QQQ)
        """
        self.symbols = symbols or ["SPY", "QQQ"]
        self.alpaca = None  # Will be injected by API layer

        # Indicator parameters
        self.ema_fast_period = 9
        self.ema_slow_period = 21
        self.rsi_period = 14
        self.volume_threshold = 2.0  # 2x average
        self.num_bars = 30  # Need 30 bars for EMA(21)

        logger.info("Momentum scanner initialized", symbols=self.symbols)

    async def scan(self, alpaca_client=None) -> List[MomentumSignal]:
        """
        Scan for momentum scalping signals.

        Returns signals only when ALL 6 conditions are met.
        Partial setups are ignored (they lead to whipsaws).

        Args:
            alpaca_client: Alpaca REST client for fetching bars

        Returns:
            List of MomentumSignal objects (may be empty if no signals)
        """
        signals: List[MomentumSignal] = []

        if not alpaca_client:
            logger.warning("Alpaca client not provided to scanner")
            return signals

        self.alpaca = alpaca_client

        try:
            # Check if we're in entry window
            if not self._is_entry_window_active():
                logger.debug("Scanner inactive - outside entry window")
                return signals

            # Scan each symbol
            for symbol in self.symbols:
                signal = await self._scan_symbol(symbol)
                if signal:
                    signals.append(signal)

            if signals:
                logger.info("Momentum signals generated", count=len(signals))

            return signals

        except Exception as e:
            logger.error("Scanner error", error=str(e), exc_info=True)
            return []

    async def _scan_symbol(self, symbol: str) -> Optional[MomentumSignal]:
        """
        Scan single symbol for momentum setup.

        Args:
            symbol: Symbol to scan (e.g., "SPY")

        Returns:
            MomentumSignal if all 6 conditions met, else None
        """
        try:
            # Fetch 1-minute bars
            bars = await self._fetch_bars(symbol)

            if not bars or len(bars) < self.num_bars:
                logger.debug("Insufficient bars for analysis", symbol=symbol, count=len(bars) if bars else 0)
                return None

            # Extract OHLCV data
            closes = [float(bar.close) for bar in bars]

            # Calculate indicators
            ema_9 = calculate_ema(closes, self.ema_fast_period)
            ema_21 = calculate_ema(closes, self.ema_slow_period)
            rsi = calculate_rsi(closes, self.rsi_period)
            vwap = calculate_vwap([self._bar_to_dict(b) for b in bars])
            relative_volume = calculate_relative_volume([self._bar_to_dict(b) for b in bars])

            if any(v is None for v in [ema_9, ema_21, rsi, vwap, relative_volume]):
                logger.debug("Missing indicator values", symbol=symbol)
                return None

            current_price = float(bars[-1].close)

            # Detect crossover
            # For MVP, we compare current vs previous bar
            if len(closes) >= 2:
                prev_ema_9 = calculate_ema(closes[:-1], self.ema_fast_period)
                prev_ema_21 = calculate_ema(closes[:-1], self.ema_slow_period)
            else:
                prev_ema_9 = None
                prev_ema_21 = None

            crossover = detect_ema_crossover(ema_9, ema_21, prev_ema_9, prev_ema_21)

            # Validate all 6 conditions
            is_valid, reason = validate_6_conditions(
                ema_crossover=crossover,
                rsi=rsi,
                relative_volume=relative_volume,
                price=current_price,
                vwap=vwap,
                in_entry_window=True,  # Already checked in scan()
                relative_strength="NEUTRAL"  # TODO: Calculate relative strength in Phase 2
            )

            if not is_valid:
                logger.debug("Signal validation failed", symbol=symbol, reason=reason)
                return None

            # All 6 conditions met - generate signal
            signal_type = "BUY" if crossover == "BULLISH" else "SELL"

            signal = self._generate_signal(
                symbol=symbol,
                signal_type=signal_type,
                ema_9=ema_9,
                ema_21=ema_21,
                rsi=rsi,
                vwap=vwap,
                relative_volume=relative_volume,
                current_price=current_price,
                reasoning=reason
            )

            logger.info("Momentum signal generated", symbol=symbol, type=signal_type, confidence=signal.confidence)
            return signal

        except Exception as e:
            logger.error("Symbol scan error", symbol=symbol, error=str(e), exc_info=True)
            return None

    async def _fetch_bars(self, symbol: str, limit: int = 30):
        """
        Fetch 1-minute bars from Alpaca.

        Args:
            symbol: Symbol (e.g., "SPY")
            limit: Number of bars to fetch (default 30)

        Returns:
            List of bar objects or None
        """
        try:
            bars = self.alpaca.get_bars(
                symbol,
                TimeFrame.Minute,
                limit=limit
            )

            if not bars or len(bars) == 0:
                logger.debug("No bars returned from Alpaca", symbol=symbol)
                return None

            # Convert to list if generator
            bar_list = list(bars.iterrows()) if hasattr(bars, 'iterrows') else bars
            if hasattr(bar_list[0], '__iter__'):
                # If returned as tuples (index, bar), extract bar
                bar_list = [b[1] if isinstance(b, tuple) else b for b in bar_list]

            return bar_list

        except Exception as e:
            logger.error("Bar fetch error", symbol=symbol, error=str(e))
            return None

    def _bar_to_dict(self, bar) -> dict:
        """Convert bar object to dict for indicator calculations."""
        return {
            'high': float(bar.high),
            'low': float(bar.low),
            'close': float(bar.close),
            'volume': int(bar.volume)
        }

    def _generate_signal(
        self,
        symbol: str,
        signal_type: str,
        ema_9: float,
        ema_21: float,
        rsi: float,
        vwap: float,
        relative_volume: float,
        current_price: float,
        reasoning: str
    ) -> MomentumSignal:
        """
        Generate momentum signal with all 6 conditions validated.

        Args:
            symbol: Symbol (SPY or QQQ)
            signal_type: "BUY" or "SELL"
            ema_9-vwap: Indicator values
            current_price: Current price
            reasoning: Why signal was generated

        Returns:
            MomentumSignal object with entry/exit levels
        """
        import uuid
        from datetime import datetime, timezone

        signal_id = str(uuid.uuid4())[:8]

        # Calculate entry/exit levels
        # For 0DTE options, we trade deltas 0.30-0.50 (moderate leverage)
        # Actual option prices will be fetched when executing trade

        if signal_type == "BUY":
            # For calls (bullish)
            entry_price = current_price
            target_1_price = current_price * 1.0075  # 0.75% gain
            target_2_price = current_price * 1.0150  # 1.50% gain
            stop_loss_price = current_price * 0.995  # 0.50% loss
        else:
            # For puts (bearish)
            entry_price = current_price
            target_1_price = current_price * 0.9925  # 0.75% gain (price down)
            target_2_price = current_price * 0.9850  # 1.50% gain
            stop_loss_price = current_price * 1.005  # 0.50% loss

        # Confidence score (all conditions met = high confidence)
        # In future, could weight by indicator strength
        confidence = 0.85  # Conservative - all conditions met

        signal = MomentumSignal(
            signal_id=signal_id,
            symbol=symbol,
            signal_type=signal_type,
            option_symbol=None,  # Will be set during execution
            confidence=confidence,
            ema_9=ema_9,
            ema_21=ema_21,
            rsi_14=rsi,
            vwap=vwap,
            relative_volume=relative_volume,
            entry_price=entry_price,
            target_1=target_1_price,
            target_2=target_2_price,
            stop_loss=stop_loss_price,
            created_at=datetime.now(timezone.utc).isoformat(),
            reasoning=reasoning
        )

        return signal

    def _is_entry_window_active(self) -> bool:
        """
        Check if current time is within entry window (9:31-11:30am ET).

        Returns:
            True if within window, False otherwise
        """
        now_et = datetime.now(timezone.utc).astimezone()

        # Entry window: 9:31am - 11:30am ET
        window_open = time(9, 31)
        window_close = time(11, 30)

        current_time = now_et.time()

        # Also check it's a trading day (Mon-Fri)
        is_trading_day = now_et.weekday() < 5  # 0-4 = Mon-Fri

        in_window = window_open <= current_time <= window_close

        return is_trading_day and in_window

    def get_health_status(self) -> Dict[str, Any]:
        """
        Get scanner health status.

        Returns:
            Dict with scanner status information
        """
        return {
            "status": "healthy",
            "symbols_monitored": self.symbols,
            "indicators_enabled": ["EMA_9", "EMA_21", "RSI_14", "VWAP", "VOLUME"],
            "entry_window_active": self._is_entry_window_active(),
            "conditions_required": 6,
            "volume_threshold": self.volume_threshold,
            "ema_periods": [self.ema_fast_period, self.ema_slow_period],
            "rsi_period": self.rsi_period,
        }


# Global scanner instance (will be created in API layer)
momentum_scanner: Optional[MomentumScanner] = None


def get_scanner() -> MomentumScanner:
    """Get global scanner instance."""
    global momentum_scanner
    if momentum_scanner is None:
        momentum_scanner = MomentumScanner()
    return momentum_scanner


logger.info("Momentum scanner module initialized")
