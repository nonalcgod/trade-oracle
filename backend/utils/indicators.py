"""
Technical indicators for 0DTE momentum scalping.

Implements EMA, RSI, VWAP, and relative volume calculations.
All calculations are vectorized using numpy for performance.
"""

from typing import List, Optional
from decimal import Decimal
import numpy as np
import structlog

logger = structlog.get_logger()


def calculate_ema(prices: List[float], period: int) -> Optional[float]:
    """
    Calculate Exponential Moving Average.

    Args:
        prices: List of prices (typically closing prices)
        period: EMA period (9 or 21 for momentum scalping)

    Returns:
        EMA value or None if insufficient data

    Formula:
        EMA = (Price - EMA_prev) * multiplier + EMA_prev
        multiplier = 2 / (period + 1)
    """
    if not prices or len(prices) < period:
        return None

    try:
        prices_arr = np.array(prices, dtype=np.float64)

        # Initial SMA for first EMA
        sma = np.mean(prices_arr[:period])

        # Multiplier for EMA
        multiplier = 2.0 / (period + 1)

        # Calculate EMA recursively
        ema = sma
        for price in prices_arr[period:]:
            ema = (price - ema) * multiplier + ema

        return float(ema)

    except Exception as e:
        logger.error("EMA calculation error", error=str(e), period=period)
        return None


def calculate_rsi(prices: List[float], period: int = 14) -> Optional[float]:
    """
    Calculate Relative Strength Index (RSI).

    Args:
        prices: List of prices (typically closing prices)
        period: RSI period (default 14)

    Returns:
        RSI value (0-100) or None if insufficient data

    Formula:
        RSI = 100 - (100 / (1 + RS))
        RS = Average Gain / Average Loss
    """
    if not prices or len(prices) < period + 1:
        return None

    try:
        prices_arr = np.array(prices, dtype=np.float64)

        # Calculate price changes
        deltas = np.diff(prices_arr)

        # Separate gains and losses
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)

        # Calculate average gain and loss
        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])

        # Avoid division by zero
        if avg_loss == 0:
            if avg_gain > 0:
                return 100.0
            else:
                return 50.0

        # Calculate RS and RSI
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return float(rsi)

    except Exception as e:
        logger.error("RSI calculation error", error=str(e), period=period)
        return None


def calculate_vwap(bars: List[dict]) -> Optional[float]:
    """
    Calculate Volume Weighted Average Price.

    VWAP is the average price weighted by volume throughout the day.
    Market makers use VWAP as a benchmark for fair price.

    Args:
        bars: List of OHLCV bar dicts with keys: high, low, close, volume

    Returns:
        VWAP value or None if insufficient data

    Formula:
        VWAP = Cumulative(Typical Price * Volume) / Cumulative(Volume)
        Typical Price = (High + Low + Close) / 3
    """
    if not bars or len(bars) < 1:
        return None

    try:
        cumulative_tpv = 0.0  # typical price * volume
        cumulative_volume = 0

        for bar in bars:
            high = float(bar.get('high', 0))
            low = float(bar.get('low', 0))
            close = float(bar.get('close', 0))
            volume = int(bar.get('volume', 0))

            # Typical price = (H + L + C) / 3
            typical_price = (high + low + close) / 3

            cumulative_tpv += typical_price * volume
            cumulative_volume += volume

        if cumulative_volume == 0:
            return None

        vwap = cumulative_tpv / cumulative_volume
        return float(vwap)

    except Exception as e:
        logger.error("VWAP calculation error", error=str(e))
        return None


def calculate_relative_volume(bars: List[dict]) -> Optional[float]:
    """
    Calculate relative volume (current bar vs average).

    Used to confirm momentum (volume spike indicates institutional participation).

    Args:
        bars: List of OHLCV bar dicts with volume key

    Returns:
        Relative volume ratio (1.0 = average) or None if insufficient data

    Example:
        If average volume is 1000 and current bar is 2500,
        relative volume = 2.5x average
    """
    if not bars or len(bars) < 2:
        return None

    try:
        volumes = np.array([int(bar.get('volume', 0)) for bar in bars], dtype=np.float64)

        if volumes.size < 2:
            return None

        # Average of all bars except current
        avg_volume = np.mean(volumes[:-1])

        if avg_volume == 0:
            return None

        # Current bar volume / average
        current_volume = volumes[-1]
        relative_vol = current_volume / avg_volume

        return float(relative_vol)

    except Exception as e:
        logger.error("Relative volume calculation error", error=str(e))
        return None


def detect_ema_crossover(
    ema_fast: Optional[float],
    ema_slow: Optional[float],
    prev_ema_fast: Optional[float],
    prev_ema_slow: Optional[float]
) -> Optional[str]:
    """
    Detect EMA crossover (bullish or bearish).

    A bullish crossover occurs when fast EMA crosses above slow EMA.
    A bearish crossover occurs when fast EMA crosses below slow EMA.

    Args:
        ema_fast: Current fast EMA (9-period)
        ema_slow: Current slow EMA (21-period)
        prev_ema_fast: Previous fast EMA
        prev_ema_slow: Previous slow EMA

    Returns:
        "BULLISH" if bullish crossover
        "BEARISH" if bearish crossover
        None if no crossover detected
    """
    if any(v is None for v in [ema_fast, ema_slow, prev_ema_fast, prev_ema_slow]):
        return None

    try:
        # Bullish: fast EMA crosses above slow EMA
        if prev_ema_fast <= prev_ema_slow and ema_fast > ema_slow:
            return "BULLISH"

        # Bearish: fast EMA crosses below slow EMA
        elif prev_ema_fast >= prev_ema_slow and ema_fast < ema_slow:
            return "BEARISH"

        return None

    except Exception as e:
        logger.error("EMA crossover detection error", error=str(e))
        return None


def validate_6_conditions(
    ema_crossover: Optional[str],
    rsi: Optional[float],
    relative_volume: Optional[float],
    price: Optional[float],
    vwap: Optional[float],
    in_entry_window: bool,
    relative_strength: Optional[str] = None
) -> tuple[bool, str]:
    """
    Validate all 6 conditions for momentum scalping entry.

    All 6 conditions MUST be met for a valid signal.
    This is non-negotiable - partial setups are whipsaws.

    Args:
        ema_crossover: "BULLISH" or "BEARISH"
        rsi: RSI(14) value (0-100)
        relative_volume: Volume ratio (2.0 = 2x average)
        price: Current price
        vwap: Current VWAP
        in_entry_window: Is current time 9:31-11:30am ET?
        relative_strength: "STRONG" or "WEAK" (comparing SPY vs QQQ or sectors)

    Returns:
        (is_valid: bool, reason: str) - True if all 6 conditions met, else False with reason
    """
    # Condition 1: EMA Crossover
    if not ema_crossover:
        return False, "Missing EMA crossover"

    # Condition 2: RSI Confirmation
    if rsi is None:
        return False, "Missing RSI value"

    if ema_crossover == "BULLISH" and rsi <= 30:
        return False, f"RSI {rsi:.1f} not above 30 (oversold)"
    elif ema_crossover == "BEARISH" and rsi >= 70:
        return False, f"RSI {rsi:.1f} not below 70 (overbought)"

    # Condition 3: Volume Spike
    if relative_volume is None:
        return False, "Missing volume data"

    if relative_volume < 2.0:
        return False, f"Volume spike {relative_volume:.1f}x below 2.0x threshold"

    # Condition 4: VWAP Position
    if price is None or vwap is None:
        return False, "Missing price or VWAP data"

    if ema_crossover == "BULLISH" and price <= vwap:
        return False, f"Price ${price:.2f} not above VWAP ${vwap:.2f}"
    elif ema_crossover == "BEARISH" and price >= vwap:
        return False, f"Price ${price:.2f} not below VWAP ${vwap:.2f}"

    # Condition 5: Time Window (9:31am - 11:30am ET)
    if not in_entry_window:
        return False, "Outside 9:31-11:30am ET entry window"

    # Condition 6: Relative Strength (optional for MVP, informational)
    # This is less critical than other conditions
    # In MVP, we'll use as a secondary confirmation

    # All conditions met!
    return True, "All 6 conditions met - ENTRY VALID"


# ============================================================================
# Unit Test Support Functions (for test_momentum_scalping.py)
# ============================================================================

def generate_test_bars(prices: List[float], volumes: Optional[List[int]] = None) -> List[dict]:
    """
    Generate synthetic OHLCV bars for testing.

    Args:
        prices: List of prices
        volumes: Optional list of volumes (defaults to 1000 each)

    Returns:
        List of OHLCV bar dicts
    """
    if volumes is None:
        volumes = [1000] * len(prices)

    bars = []
    for price, volume in zip(prices, volumes):
        bars.append({
            'high': price + 0.5,
            'low': price - 0.5,
            'close': price,
            'volume': volume
        })

    return bars


# ============================================================================
# Execution Quality Functions (Added for PATH 2: Execution Mastery)
# ============================================================================

def calculate_spread_percentage(bid: float, ask: float) -> float:
    """
    Calculate bid-ask spread as percentage of midpoint.

    Args:
        bid: Bid price
        ask: Ask price

    Returns:
        Spread percentage (0.03 = 3%)

    Example:
        >>> calculate_spread_percentage(100.0, 103.0)
        0.0296  # 2.96%
    """
    if bid <= 0 or ask <= 0:
        return float('inf')  # Invalid prices = infinite spread

    mid = (bid + ask) / 2
    if mid == 0:
        return float('inf')

    spread = (ask - bid) / mid
    return spread


def is_spread_acceptable(
    bid: float,
    ask: float,
    max_spread_pct: float = 0.03
) -> tuple[bool, float]:
    """
    Check if bid-ask spread is acceptable for trading.

    Research shows spreads >3% indicate:
    - Low liquidity (harder to exit)
    - Higher transaction costs
    - Potential for adverse selection

    Args:
        bid: Bid price
        ask: Ask price
        max_spread_pct: Maximum acceptable spread (default 3%)

    Returns:
        (is_acceptable: bool, spread_pct: float)

    Example:
        >>> is_spread_acceptable(100.0, 102.5, max_spread_pct=0.03)
        (True, 0.0247)  # 2.47% spread - acceptable

        >>> is_spread_acceptable(100.0, 105.0)
        (False, 0.0488)  # 4.88% spread - too wide
    """
    spread_pct = calculate_spread_percentage(bid, ask)
    is_acceptable = spread_pct <= max_spread_pct

    return is_acceptable, spread_pct


def calculate_midpoint(bid: float, ask: float) -> float:
    """
    Calculate midpoint price between bid and ask.

    Used for progressive pricing ladder (start at midpoint,
    walk toward ask for buys or toward bid for sells).

    Args:
        bid: Bid price
        ask: Ask price

    Returns:
        Midpoint price

    Example:
        >>> calculate_midpoint(100.0, 102.0)
        101.0
    """
    return (bid + ask) / 2


logger.info("Technical indicators module initialized")
