"""
Momentum scalping API endpoints.

Provides real-time signal generation and execution for 0DTE momentum scalping.
"""

from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
import structlog

from backend.services.momentum_scanner_mvp import (
    MomentumScanner,
    MomentumSignal,
    get_scanner,
)
from backend.api.execution import place_order_async, OrderRequest

logger = structlog.get_logger()
router = APIRouter(prefix="/api/momentum-scalping", tags=["momentum-scalping"])


class ScanResponse(BaseModel):
    """Response from scanner endpoint."""

    signals: List[MomentumSignal]
    timestamp: str
    entry_window_active: bool
    message: str = ""

    class Config:
        from_attributes = True


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    symbols_monitored: List[str]
    indicators_enabled: List[str]
    entry_window_active: bool
    vix_level: Optional[float] = None
    conditions_required: int = 6


class ExecuteSignalRequest(BaseModel):
    """Request to execute a momentum signal."""

    signal_id: str
    signal: MomentumSignal
    quantity: int = Field(default=1, ge=1, le=10)  # Number of contracts


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Check momentum scanner health.

    Returns:
        Health status of scanner and indicators
    """
    scanner = get_scanner()
    status = scanner.get_health_status()

    return HealthResponse(
        status=status.get("status", "unhealthy"),
        symbols_monitored=status.get("symbols_monitored", []),
        indicators_enabled=status.get("indicators_enabled", []),
        entry_window_active=status.get("entry_window_active", False),
        conditions_required=status.get("conditions_required", 6),
    )


@router.get("/scan", response_model=ScanResponse)
async def scan_for_signals() -> ScanResponse:
    """
    Scan for 0DTE momentum scalping signals.

    Runs scanner and returns signals where ALL 6 conditions are met.
    Partial setups are filtered out (they lead to whipsaws).

    Returns:
        ScanResponse with list of signals and metadata

    Example Response:
        {
            "signals": [
                {
                    "signal_id": "abc12345",
                    "symbol": "SPY",
                    "signal_type": "BUY",
                    "confidence": 0.85,
                    "ema_9": 590.45,
                    "ema_21": 590.20,
                    "rsi_14": 35.2,
                    "vwap": 589.80,
                    "relative_volume": 2.3,
                    "entry_price": 590.50,
                    "target_1": 595.00,
                    "target_2": 600.00,
                    "stop_loss": 585.00,
                    "created_at": "2025-11-06T09:42:15Z",
                    "reasoning": "All 6 conditions met - ENTRY VALID"
                }
            ],
            "timestamp": "2025-11-06T09:42:15Z",
            "entry_window_active": true,
            "message": "1 signal(s) generated"
        }
    """
    try:
        scanner = get_scanner()

        # Get Alpaca client from somewhere in app context
        # TODO: Inject alpaca client into scanner properly in main.py
        from backend.strategies.alpaca_integration import get_alpaca_client

        alpaca_client = get_alpaca_client()

        # Scan for signals
        signals = await scanner.scan(alpaca_client)

        # Build response
        is_in_window = scanner._is_entry_window_active()

        message = f"{len(signals)} signal(s) generated"
        if not is_in_window:
            message += " (Outside entry window)"

        response = ScanResponse(
            signals=signals,
            timestamp=datetime.now(timezone.utc).isoformat(),
            entry_window_active=is_in_window,
            message=message,
        )

        logger.info("Scan complete", signal_count=len(signals), in_window=is_in_window)

        return response

    except Exception as e:
        logger.error("Scan endpoint error", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/execute")
async def execute_signal(request: ExecuteSignalRequest) -> dict:
    """
    Execute a momentum scalping signal (place order).

    This is a MANUAL execution endpoint - user clicks "Execute" after reviewing signal.
    For MVP, we place a simple limit order on the underlying call/put option.

    Args:
        request: ExecuteSignalRequest with signal and quantity

    Returns:
        Result dict with order details

    Example Request:
        {
            "signal_id": "abc12345",
            "signal": { ... },
            "quantity": 2
        }
    """
    try:
        signal = request.signal
        quantity = request.quantity

        logger.info(
            "Executing momentum signal",
            signal_id=request.signal_id,
            symbol=signal.symbol,
            type=signal.signal_type,
            quantity=quantity,
        )

        # TODO: Implement proper option chain lookup and order placement
        # For MVP, we'll return a mock response
        # Full implementation will:
        # 1. Get 0DTE option chain for symbol
        # 2. Find best delta 0.30-0.50 strike
        # 3. Place limit order
        # 4. Create position record in database
        # 5. Set up monitoring with position_monitor

        result = {
            "status": "success",
            "signal_id": request.signal_id,
            "symbol": signal.symbol,
            "type": signal.signal_type,
            "quantity": quantity,
            "entry_price": signal.entry_price,
            "target_1": signal.target_1,
            "target_2": signal.target_2,
            "stop_loss": signal.stop_loss,
            "message": "Order prepared (MVP - manual execution ready)",
            "order_id": None,  # Will be set when order placed
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        logger.info("Signal execution response", result=result)

        return result

    except Exception as e:
        logger.error("Execute signal error", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/signal-history")
async def get_signal_history(limit: int = 10) -> dict:
    """
    Get recent momentum signals (from database).

    TODO: Implement database query to get recent signals.
    For MVP, returns empty list.

    Args:
        limit: Number of recent signals to return

    Returns:
        List of recent signals
    """
    # TODO: Query momentum_signals table
    return {
        "signals": [],
        "total_count": 0,
        "message": "Signal history not yet implemented in MVP"
    }


@router.get("/performance-metrics")
async def get_performance_metrics() -> dict:
    """
    Get momentum scalping performance metrics.

    TODO: Implement database query for win rate, P&L, etc.
    For MVP, returns placeholder.

    Returns:
        Performance metrics dict
    """
    # TODO: Calculate from trades table
    return {
        "total_trades": 0,
        "wins": 0,
        "losses": 0,
        "win_rate": 0.0,
        "profit_factor": 0.0,
        "avg_win": 0.0,
        "avg_loss": 0.0,
        "total_pnl": 0.0,
        "message": "Performance metrics not yet implemented in MVP"
    }


logger.info("Momentum scalping API endpoints initialized")
