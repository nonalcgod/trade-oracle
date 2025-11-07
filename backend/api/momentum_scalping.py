"""
Momentum scalping API endpoints.

Provides real-time signal generation and execution for 0DTE momentum scalping.
"""

from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
import structlog

from services.momentum_scanner_mvp import (
    MomentumScanner,
    MomentumSignal,
    get_scanner,
)

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


class ClosePositionRequest(BaseModel):
    """Request to close a momentum scalping position."""

    position_id: int
    exit_reason: str = "manual"  # "profit_target", "stop_loss", "manual", "time_exit", "discipline"


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

        # Get Alpaca client from execution module
        from api.execution import trading_client

        alpaca_client = trading_client

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
    Execute a momentum scalping signal with full workflow:
    1. Convert MomentumSignal → Signal model
    2. Get current portfolio state
    3. Risk validation via /api/risk/approve
    4. Place Alpaca order with fill confirmation
    5. Create position in Supabase
    6. Return execution details

    Args:
        request: ExecuteSignalRequest with signal and quantity

    Returns:
        OrderResponse dict with execution details

    Example Request:
        {
            "signal_id": "abc12345",
            "signal": { "symbol": "SPY", "signal_type": "BUY", ... },
            "quantity": 1
        }
    """
    try:
        from models.trading import Signal, SignalType
        from decimal import Decimal

        momentum_signal = request.signal
        quantity = request.quantity

        logger.info(
            "Executing momentum signal (FULL WORKFLOW)",
            signal_id=request.signal_id,
            symbol=momentum_signal.symbol,
            type=momentum_signal.signal_type,
            quantity=quantity,
        )

        # Step 1: Convert MomentumSignal → Signal model
        # For MVP, trade underlying shares (SPY/QQQ) instead of options
        entry_price = Decimal(str(momentum_signal.entry_price or 590.00))

        signal = Signal(
            symbol=momentum_signal.symbol,  # SPY or QQQ
            signal=SignalType.BUY if momentum_signal.signal_type == "BUY" else SignalType.SELL,
            strategy="0DTE Momentum Scalping",
            confidence=momentum_signal.confidence,
            entry_price=entry_price,
            stop_loss=entry_price * Decimal("0.50"),  # 50% stop loss
            take_profit=entry_price * Decimal("1.50"),  # 50% profit target
            reasoning=momentum_signal.reasoning or "6-condition momentum setup"
        )

        # Step 2: Get current portfolio state
        from api.execution import get_current_portfolio
        portfolio = await get_current_portfolio()

        # Step 3: Risk validation
        from api.risk import risk_manager
        approval = await risk_manager.approve_trade(signal, portfolio)

        if not approval.approved:
            logger.warning("Trade rejected by risk manager", reasoning=approval.reasoning)
            return {
                "success": False,
                "message": f"Trade rejected: {approval.reasoning}",
                "warning": "Risk limits exceeded",
                "signal_id": request.signal_id,
            }

        logger.info("Trade approved by risk manager",
                   position_size=approval.position_size,
                   max_loss=float(approval.max_loss))

        # Step 4: Place order (auto-creates position in database)
        from api.execution import place_limit_order
        order_response = await place_limit_order(signal, approval.position_size)

        logger.info("Order execution complete",
                   success=order_response.success,
                   alpaca_order_id=order_response.alpaca_order_id)

        return order_response.model_dump()

    except Exception as e:
        logger.error("Execute signal error", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/close-position")
async def close_momentum_position(request: ClosePositionRequest) -> dict:
    """
    Close momentum scalping position with exit reason tracking.

    Workflow:
    1. Fetch position from Supabase
    2. Close position via Alpaca
    3. Update exit reason in database
    4. Return execution details

    Args:
        request: ClosePositionRequest with position_id and exit_reason

    Returns:
        OrderResponse dict with close execution details

    Example Request:
        {
            "position_id": 123,
            "exit_reason": "manual"  # or "profit_target", "stop_loss", "discipline"
        }
    """
    try:
        from api.execution import supabase, close_position
        from models.trading import Position, ExitReason

        logger.info(
            "Closing momentum position",
            position_id=request.position_id,
            exit_reason=request.exit_reason
        )

        # Fetch position from database
        response = supabase.table("positions")\
            .select("*")\
            .eq("id", request.position_id)\
            .single()\
            .execute()

        if not response.data:
            raise HTTPException(status_code=404, detail=f"Position {request.position_id} not found")

        position = Position(**response.data)

        # Verify position is for momentum scalping strategy
        if position.strategy != "0DTE Momentum Scalping":
            raise HTTPException(
                status_code=400,
                detail=f"Position is not a momentum scalping position (strategy: {position.strategy})"
            )

        # Verify position is still open
        if position.status != "OPEN":
            return {
                "success": False,
                "message": f"Position already closed (status: {position.status})",
                "position_id": request.position_id
            }

        # Map exit reason string to ExitReason enum
        exit_reason_map = {
            "profit_target": ExitReason.PROFIT_TARGET,
            "stop_loss": ExitReason.STOP_LOSS,
            "manual": ExitReason.MANUAL,
            "time_exit": ExitReason.FORCE_CLOSE,
            "discipline": ExitReason.FORCE_CLOSE,  # 2-loss rule
        }

        exit_reason_enum = exit_reason_map.get(request.exit_reason, ExitReason.MANUAL)

        # Close via Alpaca
        order_response = await close_position(position)

        # Update exit reason in database if close succeeded
        if order_response.success:
            supabase.table("positions")\
                .update({"exit_reason": exit_reason_enum.value})\
                .eq("id", request.position_id)\
                .execute()

            logger.info(
                "Position closed successfully",
                position_id=request.position_id,
                exit_reason=exit_reason_enum.value,
                alpaca_order_id=order_response.alpaca_order_id
            )
        else:
            logger.warning(
                "Position close failed",
                position_id=request.position_id,
                error=order_response.message
            )

        return order_response.model_dump()

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Close position error", error=str(e), exc_info=True)
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


@router.get("/unusual-activity")
async def get_unusual_activity(symbols: str = "SPY,QQQ", lookback_minutes: int = 60) -> dict:
    """
    Get unusual options activity (UOA) for symbols (FREE institutional edge).

    Detects large institutional option trades that signal upcoming price moves.
    This is a FREE alternative to Unusual Whales ($48/month)!

    Detection criteria:
    - Block trades: >100 contracts with >$50K premium
    - Volume spikes: Today's volume >2x average
    - Smart money: Delta 0.30-0.70 range

    Research shows UOA provides 15-30 minute lead time on major moves.

    Args:
        symbols: Comma-separated symbols (default: "SPY,QQQ")
        lookback_minutes: How far back to scan (default: 60 minutes)

    Returns:
        Dict with:
            - signals: List of unusual activity signals
            - total_count: Number of signals detected
            - symbols_scanned: List of symbols
            - lookback_minutes: Scan period
            - generated_at: Timestamp

    Example Response:
        {
            "signals": [
                {
                    "symbol": "SPY",
                    "option_symbol": "SPY251107C00590000",
                    "signal_type": "BLOCK",
                    "side": "CALL",
                    "sentiment": "BULLISH",
                    "volume": 250,
                    "open_interest": 1000,
                    "strike": 590.0,
                    "expiration": "2025-11-07",
                    "premium": 125000,
                    "spot_price": 590.50,
                    "delta": 0.45,
                    "reasoning": "Block trade: 250 contracts @ $5.00 ($125,000 premium) | Delta: 0.45",
                    "detected_at": "2025-11-07T10:15:30Z"
                }
            ],
            "total_count": 1,
            "symbols_scanned": ["SPY", "QQQ"],
            "lookback_minutes": 60,
            "generated_at": "2025-11-07T10:30:00Z"
        }
    """
    try:
        from utils.unusual_activity import get_uoa_detector
        from api.execution import trading_client

        # Parse symbols
        symbol_list = [s.strip() for s in symbols.split(",")]

        # Get UOA detector
        uoa_detector = get_uoa_detector(trading_client)

        # Scan for unusual activity
        signals = await uoa_detector.scan_unusual_activity(symbol_list, lookback_minutes)

        logger.info("Unusual activity scan complete", count=len(signals), symbols=symbol_list)

        return {
            "signals": [s.to_dict() for s in signals],
            "total_count": len(signals),
            "symbols_scanned": symbol_list,
            "lookback_minutes": lookback_minutes,
            "generated_at": datetime.now(timezone.utc).isoformat()
        }

    except Exception as e:
        logger.error("Unusual activity API error", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/gamma-walls/{symbol}")
async def get_gamma_walls(symbol: str) -> dict:
    """
    Get gamma wall levels for a symbol (DIY institutional positioning edge).

    Calculates gamma exposure from option chains to identify:
    - Positive gamma walls (resistance levels where price struggles to break through)
    - Negative gamma walls (magnet levels that attract price)

    This is FREE alternative to $99/month SpotGamma subscription!

    Args:
        symbol: Symbol (SPY or QQQ)

    Returns:
        Dict with:
            - top_resistance_strikes: List of resistance levels
            - top_magnet_strikes: List of magnet levels
            - net_gex: Total gamma exposure
            - net_gex_interpretation: Human-readable regime
            - levels: Top 10 strikes with gamma exposure
            - spot_price: Current price
            - calculated_at: Timestamp

    Example Response:
        {
            "symbol": "SPY",
            "spot_price": 590.50,
            "top_resistance_strikes": [595.0, 600.0, 605.0],
            "top_magnet_strikes": [585.0, 580.0],
            "net_gex": 150000000,
            "net_gex_interpretation": "Positive - Moderate resistance, stabilizing market",
            "levels": [
                {"strike": 595.0, "gamma_exposure": 50000000, "type": "resistance"},
                {"strike": 585.0, "gamma_exposure": -30000000, "type": "magnet"}
            ],
            "calculated_at": "2025-11-07T10:30:15Z"
        }
    """
    try:
        from utils.gamma_walls import get_gamma_calculator
        from api.execution import trading_client

        # Get current price from Alpaca
        try:
            latest_trade = trading_client.get_latest_trade(symbol)
            current_price = float(latest_trade.price)
        except Exception as e:
            logger.warning(f"Could not fetch latest price for {symbol}, using placeholder", error=str(e))
            current_price = 590.0  # Placeholder

        # Calculate gamma walls
        gamma_calculator = get_gamma_calculator(trading_client)
        gamma_walls = await gamma_calculator.calculate_gamma_walls(symbol, current_price)

        logger.info("Gamma walls calculated via API", symbol=symbol, net_gex=gamma_walls.get('net_gex', 0))

        return gamma_walls

    except Exception as e:
        logger.error("Gamma wall API error", symbol=symbol, error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


logger.info("Momentum scalping API endpoints initialized")
