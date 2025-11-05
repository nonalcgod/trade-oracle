"""
Testing & Manual Control Endpoints

Allows manual triggering of trades and position management for testing.
DO NOT expose these endpoints in production without authentication.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from decimal import Decimal
from datetime import datetime
from typing import Optional
import structlog

from models.trading import Signal, SignalType
from api.execution import (
    close_position,
    get_open_positions,
    check_exit_conditions,
    create_position
)
from api.risk import risk_manager
from api.execution import trading_client, supabase

logger = structlog.get_logger()

router = APIRouter(prefix="/api/testing", tags=["testing"])


class ManualCloseRequest(BaseModel):
    """Request to manually close a position"""
    position_id: int
    reason: str = "Manual close via API"


class ManualSignalRequest(BaseModel):
    """Request to manually generate a signal"""
    symbol: str
    signal_type: str  # "BUY" or "SELL"
    entry_price: float
    stop_loss: float
    take_profit: float
    reasoning: str = "Manual test signal"


@router.post("/close-position")
async def manual_close_position(request: ManualCloseRequest):
    """
    Manually close a position (for testing)

    This bypasses exit conditions and immediately closes the position.
    Useful for testing the full lifecycle without waiting for conditions.
    """
    try:
        # Get all open positions
        positions = await get_open_positions()

        # Find the requested position
        position = next((p for p in positions if p.id == request.position_id), None)

        if not position:
            raise HTTPException(
                status_code=404,
                detail=f"Position {request.position_id} not found or already closed"
            )

        logger.info("Manual close requested",
                   position_id=request.position_id,
                   symbol=position.symbol,
                   reason=request.reason)

        # Close the position
        result = await close_position(position)

        if not result.success:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to close position: {result.message}"
            )

        return {
            "success": True,
            "message": f"Position {request.position_id} closed",
            "position_id": request.position_id,
            "symbol": position.symbol,
            "execution": result.execution.dict() if result.execution else None
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Manual close failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/check-exit-conditions")
async def check_all_exit_conditions():
    """
    Check exit conditions for all open positions

    Returns which positions should be exited and why.
    Does NOT actually close them - just reports status.
    """
    try:
        positions = await get_open_positions()

        if not positions:
            return {
                "open_positions": 0,
                "should_exit": [],
                "message": "No open positions to check"
            }

        results = []
        for position in positions:
            exit_reason = await check_exit_conditions(position)

            results.append({
                "position_id": position.id,
                "symbol": position.symbol,
                "entry_price": float(position.entry_price),
                "current_price": float(position.current_price) if position.current_price else None,
                "unrealized_pnl": float(position.unrealized_pnl) if position.unrealized_pnl else None,
                "should_exit": bool(exit_reason),
                "exit_reason": exit_reason
            })

        should_exit_count = sum(1 for r in results if r['should_exit'])

        return {
            "open_positions": len(positions),
            "should_exit": should_exit_count,
            "details": results,
            "message": f"{should_exit_count} position(s) meet exit conditions"
        }

    except Exception as e:
        logger.error("Exit condition check failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/force-exit-all")
async def force_exit_all_positions():
    """
    Force close ALL open positions immediately

    USE WITH CAUTION: Closes all positions regardless of P&L.
    Useful for ending a test session or emergency stop.
    """
    try:
        positions = await get_open_positions()

        if not positions:
            return {
                "success": True,
                "closed_count": 0,
                "message": "No positions to close"
            }

        logger.warning("Force exit ALL positions requested",
                      position_count=len(positions))

        results = []
        success_count = 0

        for position in positions:
            try:
                result = await close_position(position)

                results.append({
                    "position_id": position.id,
                    "symbol": position.symbol,
                    "success": result.success,
                    "message": result.message
                })

                if result.success:
                    success_count += 1

            except Exception as e:
                logger.error("Failed to close position",
                           position_id=position.id,
                           error=str(e))
                results.append({
                    "position_id": position.id,
                    "symbol": position.symbol,
                    "success": False,
                    "message": str(e)
                })

        return {
            "success": True,
            "total_positions": len(positions),
            "closed_count": success_count,
            "failed_count": len(positions) - success_count,
            "details": results
        }

    except Exception as e:
        logger.error("Force exit failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/simulate-signal")
async def simulate_trading_signal(request: ManualSignalRequest):
    """
    Generate and execute a manual trading signal

    Creates a signal, gets risk approval, and executes the trade.
    Useful for testing without waiting for real IV conditions.
    """
    try:
        # Validate signal type
        signal_type = SignalType(request.signal_type.upper())

        # Create signal
        signal = Signal(
            symbol=request.symbol,
            signal=signal_type,
            strategy="Manual Test",
            confidence=1.0,
            entry_price=Decimal(str(request.entry_price)),
            stop_loss=Decimal(str(request.stop_loss)),
            take_profit=Decimal(str(request.take_profit)),
            reasoning=request.reasoning,
            timestamp=datetime.utcnow()
        )

        # Get portfolio state
        from api.execution import get_portfolio
        portfolio_response = await get_portfolio()
        portfolio = portfolio_response.portfolio

        # Get risk approval
        approval = await risk_manager.approve_trade(signal, portfolio)

        if not approval.approved:
            return {
                "success": False,
                "stage": "risk_approval",
                "message": f"Trade rejected: {approval.reasoning}"
            }

        # Execute the trade
        from api.execution import place_limit_order, log_trade_to_supabase
        result = await place_limit_order(signal, approval.position_size)

        if not result.success:
            return {
                "success": False,
                "stage": "execution",
                "message": f"Execution failed: {result.message}"
            }

        # Create position tracking
        trade_id = await log_trade_to_supabase(result.execution, signal)

        position_id = await create_position(
            symbol=signal.symbol,
            strategy=signal.strategy,
            position_type="long" if signal_type == SignalType.BUY else "short",
            quantity=approval.position_size,
            entry_price=result.execution.entry_price,
            entry_trade_id=trade_id
        )

        return {
            "success": True,
            "signal": signal.dict(),
            "approval": approval.dict(),
            "execution": result.execution.dict() if result.execution else None,
            "position_id": position_id,
            "trade_id": trade_id,
            "message": f"Trade executed: {approval.position_size} contracts at ${float(result.execution.entry_price)}"
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid signal type: {str(e)}")
    except Exception as e:
        logger.error("Simulate signal failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/monitor-status")
async def get_monitor_status():
    """
    Get status of position monitor and what it's checking

    Returns current positions and what the monitor will do next cycle.
    """
    try:
        positions = await get_open_positions()

        status = {
            "monitor_running": True,  # Always true if backend is up
            "check_interval": "60 seconds",
            "open_positions": len(positions),
            "positions": []
        }

        for position in positions:
            exit_reason = await check_exit_conditions(position)

            status["positions"].append({
                "position_id": position.id,
                "symbol": position.symbol,
                "opened_at": position.opened_at.isoformat(),
                "unrealized_pnl": float(position.unrealized_pnl) if position.unrealized_pnl else 0,
                "will_close_next_cycle": bool(exit_reason),
                "exit_reason": exit_reason
            })

        return status

    except Exception as e:
        logger.error("Monitor status check failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def testing_health():
    """Check if testing endpoints are available"""
    return {
        "status": "ok",
        "alpaca_configured": bool(trading_client),
        "supabase_configured": bool(supabase),
        "warning": "These endpoints are for testing only - do not use in production"
    }
