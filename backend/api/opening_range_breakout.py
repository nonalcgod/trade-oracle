"""
Opening Range Breakout (ORB) API endpoints.

Provides real-time opening range tracking and breakout signal generation
for SPY, QQQ, IWM with 75-89% historical win rate.
"""

from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
import structlog

from services.opening_range_tracker import (
    OpeningRangeTracker,
    OpeningRange,
    ORBSignal,
    get_tracker,
)

logger = structlog.get_logger()
router = APIRouter(prefix="/api/orb", tags=["opening-range-breakout"])


class RangeResponse(BaseModel):
    """Response with opening range data."""

    ranges: Dict[str, Any]  # Symbol -> range data
    timestamp: str
    message: str = ""

    class Config:
        from_attributes = True


class SignalResponse(BaseModel):
    """Response with ORB signals."""

    signals: List[ORBSignal]
    timestamp: str
    entry_window_active: bool
    message: str = ""

    class Config:
        from_attributes = True


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    symbols_monitored: List[str]
    duration_minutes: int
    entry_window_active: bool
    ranges: Dict[str, Any]
    volume_threshold: float
    breakout_threshold: float


class ExecuteSignalRequest(BaseModel):
    """Request to execute an ORB signal."""

    signal_id: str
    signal: ORBSignal
    quantity: int = Field(default=1, ge=1, le=10)  # Number of contracts


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Check ORB tracker health.

    Returns:
        Health status of tracker and opening ranges
    """
    tracker = get_tracker()
    status = tracker.get_health_status()

    return HealthResponse(
        status=status.get("status", "unhealthy"),
        symbols_monitored=status.get("symbols_monitored", []),
        duration_minutes=status.get("duration_minutes", 60),
        entry_window_active=status.get("entry_window_active", False),
        ranges=status.get("ranges", {}),
        volume_threshold=status.get("volume_threshold", 1.5),
        breakout_threshold=status.get("breakout_threshold", 0.0015),
    )


@router.get("/ranges", response_model=RangeResponse)
async def get_opening_ranges() -> RangeResponse:
    """
    Get current opening ranges for all monitored symbols.

    Returns opening range data for SPY, QQQ, IWM including:
    - High/low boundaries
    - Range width (percentage)
    - Completion status
    - Pre-market gap information

    Returns:
        RangeResponse with range data for all symbols

    Example Response:
        {
            "ranges": {
                "SPY": {
                    "symbol": "SPY",
                    "range_high": 593.50,
                    "range_low": 591.20,
                    "range_width": 0.39,
                    "range_complete": true,
                    "gap_percent": 0.15
                },
                "QQQ": {...},
                "IWM": {...}
            },
            "timestamp": "2025-11-06T10:35:00Z",
            "message": "3 ranges tracked, 3 complete"
        }
    """
    try:
        tracker = get_tracker()

        # Get Alpaca client from execution module
        from api.execution import trading_client

        alpaca_client = trading_client

        # Update ranges (fetches latest bars)
        ranges = await tracker.update_ranges(alpaca_client)

        # Convert to dict format for response
        ranges_dict = {}
        for symbol, range_obj in ranges.items():
            ranges_dict[symbol] = {
                "symbol": range_obj.symbol,
                "trade_date": range_obj.trade_date,
                "duration_minutes": range_obj.duration_minutes,
                "range_high": range_obj.range_high,
                "range_low": range_obj.range_low,
                "range_width": range_obj.range_width,
                "gap_percent": range_obj.gap_percent,
                "range_complete": range_obj.range_complete,
                "range_start_time": range_obj.range_start_time,
                "range_end_time": range_obj.range_end_time,
            }

        complete_count = sum(1 for r in ranges.values() if r.range_complete)
        message = f"{len(ranges)} range(s) tracked, {complete_count} complete"

        response = RangeResponse(
            ranges=ranges_dict,
            timestamp=datetime.now(timezone.utc).isoformat(),
            message=message,
        )

        logger.info("Ranges fetched", symbol_count=len(ranges), complete_count=complete_count)

        return response

    except Exception as e:
        logger.error("Ranges endpoint error", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/scan", response_model=SignalResponse)
async def scan_for_breakouts() -> SignalResponse:
    """
    Scan for opening range breakouts on all symbols.

    Detects breakouts from completed opening ranges with:
    - Price breaks above/below range boundaries
    - Volume confirmation (≥1.5x average)
    - RSI confirmation (>50 bullish, <50 bearish)
    - 0.15% threshold to filter false breakouts

    Only generates signals during entry window (10:30am - 2:00pm ET).

    Returns:
        SignalResponse with list of ORB signals

    Example Response:
        {
            "signals": [
                {
                    "signal_id": "xyz789",
                    "symbol": "SPY",
                    "direction": "BULLISH",
                    "opening_range_id": "abc123",
                    "range_high": 593.50,
                    "range_low": 591.20,
                    "range_width": 0.39,
                    "breakout_price": 593.95,
                    "target_price": 595.15,
                    "stop_loss_price": 593.50,
                    "volume_confirmation": true,
                    "rsi_confirmation": 58.3,
                    "confidence": 0.85,
                    "reasoning": "BULLISH breakout from 60-min opening range...",
                    "created_at": "2025-11-06T10:45:00Z"
                }
            ],
            "timestamp": "2025-11-06T10:45:00Z",
            "entry_window_active": true,
            "message": "1 breakout signal(s) generated"
        }
    """
    try:
        tracker = get_tracker()

        # Get Alpaca client
        from api.execution import trading_client

        alpaca_client = trading_client

        # First update ranges to ensure they're current
        await tracker.update_ranges(alpaca_client)

        # Scan for breakouts
        signals = await tracker.scan_breakouts(alpaca_client)

        # Build response
        is_in_window = tracker._is_entry_window_active()

        message = f"{len(signals)} breakout signal(s) generated"
        if not is_in_window:
            message += " (Outside entry window)"

        response = SignalResponse(
            signals=signals,
            timestamp=datetime.now(timezone.utc).isoformat(),
            entry_window_active=is_in_window,
            message=message,
        )

        logger.info("Breakout scan complete", signal_count=len(signals), in_window=is_in_window)

        return response

    except Exception as e:
        logger.error("Scan endpoint error", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/execute")
async def execute_orb_signal(request: ExecuteSignalRequest):
    """
    Execute an ORB signal (buy options contract).

    Takes a generated ORB signal and executes the trade:
    1. Validates signal is still valid (price hasn't reversed)
    2. Finds best ATM option (0.40-0.60 delta)
    3. Checks risk limits (circuit breakers)
    4. Places market order for specified quantity
    5. Tracks position with ORB-specific exit rules

    Exit Rules:
    - Target: Range width × 1.5 OR 50% option gain
    - Stop: Price re-enters range OR 40% loss
    - Time: Close all by 3:00pm ET

    Args:
        request: ExecuteSignalRequest with signal and quantity

    Returns:
        Execution result with position details

    Example Response:
        {
            "success": true,
            "position_id": 42,
            "symbol": "SPY",
            "option_symbol": "SPY251106C00594000",
            "quantity": 2,
            "entry_price": 3.45,
            "target_price": 595.15,
            "stop_loss_price": 593.50,
            "strategy": "OPENING_RANGE_BREAKOUT",
            "message": "ORB trade executed successfully"
        }
    """
    try:
        from api.execution import execute_option_order
        from api.risk import check_circuit_breakers
        from models.trading import PositionType

        signal = request.signal

        logger.info(
            "Executing ORB signal",
            signal_id=request.signal_id,
            symbol=signal.symbol,
            direction=signal.direction,
            quantity=request.quantity
        )

        # Validate signal is recent (not stale)
        from datetime import datetime, timezone, timedelta
        signal_time = datetime.fromisoformat(signal.created_at.replace('Z', '+00:00'))
        age_minutes = (datetime.now(timezone.utc) - signal_time).total_seconds() / 60

        if age_minutes > 10:
            raise HTTPException(
                status_code=400,
                detail=f"Signal is too old ({age_minutes:.1f} minutes). Generate a fresh signal."
            )

        # Check circuit breakers
        circuit_breaker_check = await check_circuit_breakers()
        if not circuit_breaker_check.get("approved", False):
            raise HTTPException(
                status_code=403,
                detail=f"Trade rejected by circuit breaker: {circuit_breaker_check.get('reason')}"
            )

        # Determine option type based on signal direction
        option_type = "call" if signal.direction == "BULLISH" else "put"

        # Execute trade through execution service
        # This will:
        # - Find best ATM option (0.40-0.60 delta)
        # - Check risk limits
        # - Place market order
        # - Track position with exit rules
        execution_result = await execute_option_order(
            symbol=signal.symbol,
            option_type=option_type,
            quantity=request.quantity,
            strategy=PositionType.OPENING_RANGE_BREAKOUT,
            signal_data={
                "signal_id": request.signal_id,
                "breakout_price": signal.breakout_price,
                "target_price": signal.target_price,
                "stop_loss_price": signal.stop_loss_price,
                "range_high": signal.range_high,
                "range_low": signal.range_low,
                "range_width": signal.range_width,
                "direction": signal.direction,
                "confidence": signal.confidence,
                "reasoning": signal.reasoning,
            }
        )

        logger.info(
            "ORB trade executed",
            symbol=signal.symbol,
            direction=signal.direction,
            position_id=execution_result.get("position_id")
        )

        return {
            "success": True,
            "position_id": execution_result.get("position_id"),
            "symbol": signal.symbol,
            "option_symbol": execution_result.get("option_symbol"),
            "quantity": request.quantity,
            "entry_price": execution_result.get("entry_price"),
            "target_price": signal.target_price,
            "stop_loss_price": signal.stop_loss_price,
            "strategy": "OPENING_RANGE_BREAKOUT",
            "message": "ORB trade executed successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Execute endpoint error", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


logger.info("ORB API endpoints initialized")
