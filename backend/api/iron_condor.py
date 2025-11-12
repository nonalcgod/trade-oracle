"""
Iron Condor API Routes

Endpoints for 0DTE iron condor strategy.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from decimal import Decimal
from datetime import datetime, timedelta
from typing import Optional
import os
import structlog
from alpaca.data import OptionHistoricalDataClient, StockHistoricalDataClient

from models.strategies import IronCondorSignal, IronCondorSetup
from strategies.iron_condor import IronCondorStrategy

logger = structlog.get_logger()

router = APIRouter(prefix="/api/iron-condor", tags=["iron_condor"])

# Initialize Alpaca Data Clients
ALPACA_API_KEY = os.getenv("ALPACA_API_KEY")
ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")

option_client: Optional[OptionHistoricalDataClient] = None
stock_client: Optional[StockHistoricalDataClient] = None
strategy: Optional[IronCondorStrategy] = None

try:
    if ALPACA_API_KEY and ALPACA_SECRET_KEY:
        option_client = OptionHistoricalDataClient(ALPACA_API_KEY, ALPACA_SECRET_KEY)
        stock_client = StockHistoricalDataClient(ALPACA_API_KEY, ALPACA_SECRET_KEY)
        strategy = IronCondorStrategy(option_client, stock_client)
        logger.info("Iron condor strategy initialized")
except Exception as e:
    logger.error("Failed to initialize iron condor strategy", error=str(e))


class GenerateSignalRequest(BaseModel):
    """Request to generate iron condor signal"""
    underlying: str = "SPY"  # Default to SPY
    expiration_date: Optional[str] = None  # YYYY-MM-DD, defaults to today (0DTE)
    quantity: int = 1


class CheckExitRequest(BaseModel):
    """Request to check exit conditions"""
    setup: IronCondorSetup
    current_value: Decimal  # Current market value of position


@router.post("/signal")
async def generate_signal(request: GenerateSignalRequest) -> dict:
    """
    Generate iron condor entry signal

    Args:
        request: Configuration (underlying, expiration, quantity)

    Returns:
        IronCondorSignal if conditions met, or status message
    """
    try:
        if not strategy:
            raise HTTPException(status_code=503, detail="Strategy not initialized")

        # Parse expiration date (default to today for 0DTE)
        if request.expiration_date:
            expiration = datetime.strptime(request.expiration_date, "%Y-%m-%d")
        else:
            expiration = datetime.now().replace(hour=16, minute=0, second=0)  # 4pm today

        logger.info("Generating iron condor signal",
                   underlying=request.underlying,
                   expiration=expiration.date(),
                   quantity=request.quantity)

        # Generate signal
        signal = await strategy.generate_signal(
            request.underlying,
            expiration,
            request.quantity
        )

        if signal:
            return {
                "status": "signal_generated",
                "signal": signal.dict(),
                "message": f"Iron condor signal for {request.underlying}"
            }
        else:
            return {
                "status": "no_signal",
                "message": "No iron condor signal (not in entry window or conditions not met)"
            }

    except Exception as e:
        logger.error("Failed to generate signal", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/check-exit")
async def check_exit(request: CheckExitRequest) -> dict:
    """
    Check if iron condor should be exited

    Args:
        request: Setup and current value

    Returns:
        Exit decision with reason
    """
    try:
        if not strategy:
            raise HTTPException(status_code=503, detail="Strategy not initialized")

        should_exit, reason = await strategy.check_exit_conditions(
            request.setup,
            request.current_value
        )

        return {
            "should_exit": should_exit,
            "reason": reason,
            "current_value": float(request.current_value),
            "entry_credit": float(request.setup.total_credit)
        }

    except Exception as e:
        logger.error("Failed to check exit", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/build")
async def build_iron_condor(
    underlying: str = "SPY",
    expiration_date: Optional[str] = None,
    quantity: int = 1
) -> dict:
    """
    Build iron condor with strike selection

    Args:
        underlying: Underlying symbol
        expiration_date: Expiration (YYYY-MM-DD), defaults to today
        quantity: Number of iron condors

    Returns:
        IronCondorSetup with all strikes and pricing
    """
    try:
        if not strategy:
            raise HTTPException(status_code=503, detail="Strategy not initialized")

        # Parse expiration
        if expiration_date:
            expiration = datetime.strptime(expiration_date, "%Y-%m-%d")
        else:
            expiration = datetime.now().replace(hour=16, minute=0, second=0)

        logger.info("Building iron condor",
                   underlying=underlying,
                   expiration=expiration.date())

        setup = await strategy.build_iron_condor(underlying, expiration, quantity)

        if setup:
            # Also return the multi-leg order structure
            multi_leg_order = strategy.create_multi_leg_order(setup)

            return {
                "status": "success",
                "setup": setup.dict(),
                "multi_leg_order": multi_leg_order.dict(),
                "message": f"Iron condor built for {underlying}"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to build iron condor")

    except Exception as e:
        logger.error("Failed to build iron condor", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/should-enter")
async def should_enter_now() -> dict:
    """
    Check if current time is in entry window

    Returns:
        Boolean indicating if should consider entering
    """
    try:
        if not strategy:
            raise HTTPException(status_code=503, detail="Strategy not initialized")

        should_enter = await strategy.should_enter_now()

        # Get current time in ET for display
        from zoneinfo import ZoneInfo
        now_et = datetime.now(ZoneInfo("America/New_York"))

        return {
            "should_enter": should_enter,
            "entry_window": "9:31am - 9:45am ET",
            "current_time": now_et.strftime("%H:%M:%S ET")
        }

    except Exception as e:
        logger.error("Failed to check entry time", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """Check if iron condor strategy is operational"""
    return {
        "status": "ok",
        "strategy_initialized": bool(strategy),
        "option_client_configured": bool(option_client),
        "stock_client_configured": bool(stock_client)
    }
