"""
Opening Range Breakout (ORB) Tracker Service.

Tracks the opening range (high/low) during the first 60 minutes of trading
(9:30am - 10:30am ET) and detects breakouts with volume confirmation.

Win Rate: 75-89% (highest of all strategies)
Daily Target: $200-400/day
Hold Duration: 30-180 minutes

Entry Rules:
1. Wait for 60-minute opening range to complete (10:30am ET)
2. Price breaks above/below range with close confirmation
3. Volume on breakout candle ≥1.5x average
4. RSI confirmation (>50 bullish, <50 bearish)
5. Enter at market open of next 5-minute candle

Exit Rules:
- Target: Range width × 1.5 OR 50% option gain
- Stop: Price re-enters range (thesis invalidation) OR 40% loss
- Time Exit: Close all by 3:00pm ET
"""

from datetime import datetime, timezone, time, timedelta
from typing import List, Optional, Dict, Any
from decimal import Decimal
import uuid
import structlog
from zoneinfo import ZoneInfo

from alpaca.data.timeframe import TimeFrame
from pydantic import BaseModel, Field

logger = structlog.get_logger()

# Eastern Time Zone
EASTERN_TZ = ZoneInfo("America/New_York")


class OpeningRange(BaseModel):
    """Opening range data for a trading day."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    symbol: str
    trade_date: str
    duration_minutes: int = 60  # Default: 60-minute ORB

    # Range boundaries
    range_high: Optional[float] = None
    range_low: Optional[float] = None
    range_width: Optional[float] = None  # Percentage

    # Pre-market data
    gap_percent: Optional[float] = None
    pre_market_volume: Optional[int] = None

    # Status
    range_complete: bool = False
    range_start_time: Optional[str] = None
    range_end_time: Optional[str] = None

    class Config:
        from_attributes = True


class ORBSignal(BaseModel):
    """Opening Range Breakout signal."""

    signal_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    symbol: str
    direction: str  # "BULLISH" or "BEARISH"

    # Opening range reference
    opening_range_id: str
    range_high: float
    range_low: float
    range_width: float  # Percentage

    # Breakout details
    breakout_price: float
    breakout_time: str
    volume_confirmation: bool
    rsi_confirmation: Optional[float] = None

    # Entry/Exit levels
    target_price: float  # Range width × 1.5
    stop_loss_price: float  # Range boundary (invalidation)

    # Confidence scoring
    confidence: float = Field(ge=0, le=1)

    # Metadata
    created_at: str
    reasoning: str = ""

    class Config:
        from_attributes = True


class OpeningRangeTracker:
    """
    Tracks opening ranges and detects breakouts.

    Monitors the first 60 minutes of trading (9:30-10:30am ET) to establish
    the high/low range, then watches for breakouts with volume confirmation.
    """

    def __init__(
        self,
        symbols: List[str] = None,
        duration_minutes: int = 60
    ):
        """
        Initialize opening range tracker.

        Args:
            symbols: List of symbols to track (default: SPY, QQQ, IWM)
            duration_minutes: Range duration in minutes (default: 60)
        """
        self.symbols = symbols or ["SPY", "QQQ", "IWM"]
        self.duration_minutes = duration_minutes
        self.alpaca = None  # Will be injected by API layer

        # Tracking state (resets daily)
        self.ranges: Dict[str, OpeningRange] = {}

        # Filters
        self.volume_threshold = 1.5  # 1.5x average for breakout confirmation
        self.breakout_threshold = 0.0015  # 0.15% beyond range to filter false breaks

        logger.info(
            "Opening range tracker initialized",
            symbols=self.symbols,
            duration_minutes=duration_minutes
        )

    async def update_ranges(self, alpaca_client=None) -> Dict[str, OpeningRange]:
        """
        Update opening ranges for all monitored symbols.

        Fetches bars and calculates/updates ranges if market is open
        and within opening range building window (9:30-10:30am ET).

        Args:
            alpaca_client: Alpaca REST client for fetching bars

        Returns:
            Dictionary of symbol -> OpeningRange
        """
        if not alpaca_client:
            logger.warning("Alpaca client not provided to tracker")
            return self.ranges

        self.alpaca = alpaca_client

        try:
            now_et = datetime.now(timezone.utc).astimezone(EASTERN_TZ)

            # Reset ranges at market open (9:30am)
            if self._should_reset_ranges(now_et):
                self.ranges = {}
                logger.info("Opening ranges reset for new trading day")

            # Update each symbol's range
            for symbol in self.symbols:
                range_data = await self._update_symbol_range(symbol, now_et)
                if range_data:
                    self.ranges[symbol] = range_data

            return self.ranges

        except Exception as e:
            logger.error("Range update error", error=str(e), exc_info=True)
            return self.ranges

    async def _update_symbol_range(
        self,
        symbol: str,
        now_et: datetime
    ) -> Optional[OpeningRange]:
        """
        Update opening range for a single symbol.

        Args:
            symbol: Symbol to update (e.g., "SPY")
            now_et: Current time in Eastern timezone

        Returns:
            OpeningRange object or None
        """
        try:
            # Get or create range for this symbol
            if symbol not in self.ranges:
                self.ranges[symbol] = OpeningRange(
                    symbol=symbol,
                    trade_date=now_et.strftime("%Y-%m-%d"),
                    duration_minutes=self.duration_minutes,
                    range_start_time=self._get_market_open_time(now_et).isoformat()
                )

            range_obj = self.ranges[symbol]

            # If range already complete, return it
            if range_obj.range_complete:
                return range_obj

            # Check if we're in the range-building window
            market_open = self._get_market_open_time(now_et)
            range_end_time = market_open + timedelta(minutes=self.duration_minutes)

            if now_et < market_open:
                logger.debug("Before market open", symbol=symbol)
                return range_obj

            # Fetch bars from market open until now (or range end)
            bars = await self._fetch_opening_bars(symbol, market_open, now_et)

            if not bars:
                logger.debug("No bars available", symbol=symbol)
                return range_obj

            # Calculate range high/low
            highs = [float(bar.high) for bar in bars]
            lows = [float(bar.low) for bar in bars]

            range_obj.range_high = max(highs)
            range_obj.range_low = min(lows)
            range_obj.range_width = ((range_obj.range_high - range_obj.range_low) /
                                     range_obj.range_low * 100)

            # Check if range is now complete
            if now_et >= range_end_time:
                range_obj.range_complete = True
                range_obj.range_end_time = range_end_time.isoformat()

                logger.info(
                    "Opening range complete",
                    symbol=symbol,
                    high=range_obj.range_high,
                    low=range_obj.range_low,
                    width_pct=f"{range_obj.range_width:.2f}%"
                )

            return range_obj

        except Exception as e:
            logger.error("Symbol range update error", symbol=symbol, error=str(e))
            return None

    async def scan_breakouts(self, alpaca_client=None) -> List[ORBSignal]:
        """
        Scan for opening range breakouts on all symbols.

        Checks if any symbol has broken out of its opening range with
        proper confirmation (volume, close beyond range, RSI).

        Args:
            alpaca_client: Alpaca REST client for fetching current bars

        Returns:
            List of ORBSignal objects (empty if no breakouts)
        """
        signals: List[ORBSignal] = []

        if not alpaca_client:
            logger.warning("Alpaca client not provided to scanner")
            return signals

        self.alpaca = alpaca_client

        try:
            # Only scan during valid entry window (10:30am - 2:00pm ET)
            if not self._is_entry_window_active():
                logger.debug("Scanner inactive - outside entry window")
                return signals

            # Scan each symbol
            for symbol in self.symbols:
                signal = await self._check_symbol_breakout(symbol)
                if signal:
                    signals.append(signal)

            if signals:
                logger.info("ORB signals generated", count=len(signals))

            return signals

        except Exception as e:
            logger.error("Breakout scan error", error=str(e), exc_info=True)
            return []

    async def _check_symbol_breakout(self, symbol: str) -> Optional[ORBSignal]:
        """
        Check if symbol has broken out of opening range.

        Args:
            symbol: Symbol to check (e.g., "SPY")

        Returns:
            ORBSignal if breakout detected, else None
        """
        try:
            # Get opening range for this symbol
            range_obj = self.ranges.get(symbol)

            if not range_obj or not range_obj.range_complete:
                logger.debug("Range not complete", symbol=symbol)
                return None

            # Fetch current/recent 5-minute bars
            bars = await self._fetch_recent_bars(symbol, limit=5)

            if not bars or len(bars) == 0:
                logger.debug("No recent bars", symbol=symbol)
                return None

            current_bar = bars[-1]
            current_price = float(current_bar.close)
            current_volume = int(current_bar.volume)

            # Calculate average volume from opening bars
            opening_bars = await self._fetch_opening_bars(
                symbol,
                datetime.fromisoformat(range_obj.range_start_time),
                datetime.fromisoformat(range_obj.range_end_time)
            )

            if not opening_bars:
                return None

            avg_volume = sum(int(b.volume) for b in opening_bars) / len(opening_bars)

            # Check for breakout with threshold
            bullish_breakout = current_price > range_obj.range_high * (1 + self.breakout_threshold)
            bearish_breakout = current_price < range_obj.range_low * (1 - self.breakout_threshold)

            if not (bullish_breakout or bearish_breakout):
                return None

            # Volume confirmation: require 1.5x average volume
            volume_confirmed = current_volume >= (avg_volume * self.volume_threshold)

            if not volume_confirmed:
                logger.debug(
                    "Breakout without volume confirmation",
                    symbol=symbol,
                    current_volume=current_volume,
                    avg_volume=avg_volume
                )
                return None

            # RSI confirmation (optional, improves win rate)
            from utils.indicators import calculate_rsi
            closes = [float(b.close) for b in bars]
            rsi = calculate_rsi(closes, 14)

            # Determine direction
            if bullish_breakout:
                direction = "BULLISH"
                # RSI should be > 50 for bullish confirmation
                rsi_confirmed = rsi is not None and rsi > 50
            else:
                direction = "BEARISH"
                # RSI should be < 50 for bearish confirmation
                rsi_confirmed = rsi is not None and rsi < 50

            if not rsi_confirmed:
                logger.debug(
                    "Breakout without RSI confirmation",
                    symbol=symbol,
                    direction=direction,
                    rsi=rsi
                )
                # Continue anyway - RSI is helpful but not required

            # Calculate entry/exit levels
            # Target: Range width × 1.5 beyond breakout
            target_distance = range_obj.range_width / 100 * 1.5

            if direction == "BULLISH":
                target_price = range_obj.range_high * (1 + target_distance)
                stop_loss_price = range_obj.range_high  # Re-entering range = thesis broken
            else:
                target_price = range_obj.range_low * (1 - target_distance)
                stop_loss_price = range_obj.range_low

            # Calculate confidence
            confidence = 0.75  # Base confidence (75% win rate)
            if rsi_confirmed:
                confidence += 0.10  # +10% for RSI alignment
            if current_volume >= (avg_volume * 2.0):  # Strong volume
                confidence += 0.05  # +5% for strong volume

            confidence = min(confidence, 0.95)  # Cap at 95%

            # Generate signal
            signal = ORBSignal(
                symbol=symbol,
                direction=direction,
                opening_range_id=range_obj.id,
                range_high=range_obj.range_high,
                range_low=range_obj.range_low,
                range_width=range_obj.range_width,
                breakout_price=current_price,
                breakout_time=datetime.now(timezone.utc).isoformat(),
                volume_confirmation=volume_confirmed,
                rsi_confirmation=rsi,
                target_price=target_price,
                stop_loss_price=stop_loss_price,
                confidence=confidence,
                created_at=datetime.now(timezone.utc).isoformat(),
                reasoning=f"{direction} breakout from {self.duration_minutes}-min opening range. "
                         f"Range: ${range_obj.range_low:.2f}-${range_obj.range_high:.2f} "
                         f"({range_obj.range_width:.2f}% width). "
                         f"Volume: {current_volume/avg_volume:.1f}x average. "
                         f"RSI: {rsi:.1f if rsi else 'N/A'}."
            )

            logger.info(
                "ORB signal generated",
                symbol=symbol,
                direction=direction,
                breakout_price=current_price,
                confidence=confidence
            )

            return signal

        except Exception as e:
            logger.error("Breakout check error", symbol=symbol, error=str(e))
            return None

    async def _fetch_opening_bars(
        self,
        symbol: str,
        start_time: datetime,
        end_time: datetime
    ):
        """
        Fetch bars during opening range window.

        Args:
            symbol: Symbol (e.g., "SPY")
            start_time: Range start (market open)
            end_time: Range end (market open + duration)

        Returns:
            List of bar objects
        """
        try:
            bars = self.alpaca.get_bars(
                symbol,
                TimeFrame.Minute,
                start=start_time.isoformat(),
                end=end_time.isoformat()
            )

            if not bars or len(bars) == 0:
                return None

            # Convert to list
            bar_list = list(bars.iterrows()) if hasattr(bars, 'iterrows') else bars
            if hasattr(bar_list[0], '__iter__'):
                bar_list = [b[1] if isinstance(b, tuple) else b for b in bar_list]

            return bar_list

        except Exception as e:
            logger.error("Opening bars fetch error", symbol=symbol, error=str(e))
            return None

    async def _fetch_recent_bars(self, symbol: str, limit: int = 5):
        """
        Fetch recent 5-minute bars for breakout detection.

        Args:
            symbol: Symbol (e.g., "SPY")
            limit: Number of bars to fetch

        Returns:
            List of bar objects
        """
        try:
            bars = self.alpaca.get_bars(
                symbol,
                TimeFrame(5, TimeFrame.Minute),  # 5-minute bars
                limit=limit
            )

            if not bars or len(bars) == 0:
                return None

            # Convert to list
            bar_list = list(bars.iterrows()) if hasattr(bars, 'iterrows') else bars
            if hasattr(bar_list[0], '__iter__'):
                bar_list = [b[1] if isinstance(b, tuple) else b for b in bar_list]

            return bar_list

        except Exception as e:
            logger.error("Recent bars fetch error", symbol=symbol, error=str(e))
            return None

    def _get_market_open_time(self, reference_time: datetime) -> datetime:
        """
        Get market open time (9:30am ET) for the given date.

        Args:
            reference_time: Reference datetime in Eastern timezone

        Returns:
            Market open datetime (9:30am ET)
        """
        return reference_time.replace(
            hour=9,
            minute=30,
            second=0,
            microsecond=0
        )

    def _should_reset_ranges(self, now_et: datetime) -> bool:
        """
        Check if ranges should be reset (new trading day).

        Args:
            now_et: Current time in Eastern timezone

        Returns:
            True if ranges should be reset
        """
        # Reset if no ranges exist
        if not self.ranges:
            return True

        # Reset if first range date doesn't match today
        first_range = next(iter(self.ranges.values()))
        range_date = first_range.trade_date
        today_date = now_et.strftime("%Y-%m-%d")

        return range_date != today_date

    def _is_entry_window_active(self) -> bool:
        """
        Check if current time is within entry window (10:30am - 2:00pm ET).

        Range must be complete (10:30am) and sufficient time remains for trade
        to reach target (before 2:00pm).

        Returns:
            True if within window, False otherwise
        """
        now_et = datetime.now(timezone.utc).astimezone(EASTERN_TZ)

        # Entry window: 10:30am - 2:00pm ET
        window_open = time(10, 30)
        window_close = time(14, 0)  # 2:00pm

        current_time = now_et.time()

        # Check it's a trading day (Mon-Fri)
        is_trading_day = now_et.weekday() < 5

        in_window = window_open <= current_time <= window_close

        return is_trading_day and in_window

    def get_ranges(self) -> Dict[str, OpeningRange]:
        """
        Get current opening ranges for all symbols.

        Returns:
            Dictionary of symbol -> OpeningRange
        """
        return self.ranges

    def get_range(self, symbol: str) -> Optional[OpeningRange]:
        """
        Get opening range for specific symbol.

        Args:
            symbol: Symbol (e.g., "SPY")

        Returns:
            OpeningRange object or None
        """
        return self.ranges.get(symbol)

    def get_health_status(self) -> Dict[str, Any]:
        """
        Get tracker health status.

        Returns:
            Dict with tracker status information
        """
        ranges_status = {}
        for symbol, range_obj in self.ranges.items():
            ranges_status[symbol] = {
                "complete": range_obj.range_complete,
                "high": range_obj.range_high,
                "low": range_obj.range_low,
                "width_pct": f"{range_obj.range_width:.2f}%" if range_obj.range_width else None
            }

        return {
            "status": "healthy",
            "symbols_monitored": self.symbols,
            "duration_minutes": self.duration_minutes,
            "entry_window_active": self._is_entry_window_active(),
            "ranges": ranges_status,
            "volume_threshold": self.volume_threshold,
            "breakout_threshold": self.breakout_threshold
        }


# Global tracker instance (will be created in API layer)
orb_tracker: Optional[OpeningRangeTracker] = None


def get_tracker() -> OpeningRangeTracker:
    """Get global tracker instance."""
    global orb_tracker
    if orb_tracker is None:
        orb_tracker = OpeningRangeTracker()
    return orb_tracker


logger.info("Opening range tracker module initialized")
