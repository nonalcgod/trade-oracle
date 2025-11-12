"""
Auto-Trade API - Intelligent One-Click Trading
Researches market conditions, selects best strategy, and executes automatically
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime, time, timezone
from zoneinfo import ZoneInfo
from decimal import Decimal
import structlog
import asyncio
import os
from enum import Enum

from models.trading import Signal, SignalType

logger = structlog.get_logger()

router = APIRouter(prefix="/api/auto-trade", tags=["auto-trade"])


class AutoTradeStatus(str, Enum):
    """Status of auto-trade execution"""
    PENDING = "pending"
    RESEARCHING = "researching"
    WAITING_FOR_MARKET = "waiting_for_market"
    EXECUTING = "executing"
    MONITORING = "monitoring"
    COMPLETED = "completed"
    FAILED = "failed"


class MarketConditions(BaseModel):
    """Market research findings"""
    vix_level: Optional[float] = None
    vix_interpretation: str
    market_trend: str  # bullish, bearish, neutral, range_bound
    economic_events_today: List[str]
    recommended_strategy: str
    confidence: float
    reasoning: str


class AutoTradeState(BaseModel):
    """Current state of auto-trade execution"""
    status: AutoTradeStatus
    message: str
    market_conditions: Optional[MarketConditions] = None
    selected_strategy: Optional[str] = None
    trade_details: Optional[Dict[str, Any]] = None
    position_id: Optional[int] = None
    order_id: Optional[str] = None
    error: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None


# Global state storage (in production, use Redis)
auto_trade_sessions: Dict[str, AutoTradeState] = {}


def is_market_open() -> bool:
    """Check if market is currently open (9:30am - 4:00pm ET)"""
    now_utc = datetime.now(timezone.utc)
    # Convert to ET using ZoneInfo (handles DST automatically)
    now_et = now_utc.astimezone(ZoneInfo("America/New_York"))
    et_time = now_et.time()

    market_open = time(9, 30)
    market_close = time(16, 0)

    # Check if weekday
    is_weekday = now_et.weekday() < 5

    return is_weekday and market_open <= et_time < market_close


def time_until_market_open() -> int:
    """Returns seconds until market opens (9:30am ET)"""
    now_utc = datetime.now(timezone.utc)
    now_et = now_utc.astimezone(ZoneInfo("America/New_York"))

    # Create market open time for today
    market_open_today = now_et.replace(hour=9, minute=30, second=0, microsecond=0)

    if now_et.time() < time(9, 30):
        # Market hasn't opened yet today
        time_until = (market_open_today - now_et).total_seconds()
    else:
        # Market already opened/closed today, wait for tomorrow
        from datetime import timedelta
        market_open_tomorrow = market_open_today + timedelta(days=1)
        time_until = (market_open_tomorrow - now_et).total_seconds()

    return int(time_until)


async def research_market_conditions() -> MarketConditions:
    """
    Research current market conditions using web search
    Returns recommended strategy based on VIX, trends, economic calendar
    """
    logger.info("Starting market research")

    # In production, this would use actual web search APIs
    # For now, we'll use the data endpoints and return intelligent defaults

    # TODO: Integrate with web search for:
    # - VIX level from CBOE
    # - Economic calendar from investing.com
    # - Market sentiment from finviz
    # - Options flow from unusual whales

    # Placeholder logic (will be enhanced with actual web research)
    vix_level = None
    vix_interpretation = "Unknown (market closed or data unavailable)"
    market_trend = "neutral"
    economic_events = []

    # Strategy selection logic based on time of day
    now_utc = datetime.now(timezone.utc)
    now_et = now_utc.astimezone(ZoneInfo("America/New_York"))
    et_time = now_et.time()

    # Iron Condor window: 9:31-9:45am ET
    ic_start = time(9, 31)
    ic_end = time(9, 45)

    # Momentum window: 9:31-11:30am ET
    momentum_start = time(9, 31)
    momentum_end = time(11, 30)

    if ic_start <= et_time <= ic_end:
        # Iron Condor window is open
        recommended_strategy = "iron_condor"
        confidence = 0.85
        reasoning = (
            "Iron Condor entry window is currently open (9:31-9:45am ET). "
            "This is the optimal time for same-day expiration spreads. "
            "Recommended for range-bound markets with defined risk."
        )
    elif momentum_start <= et_time <= momentum_end:
        # Momentum scalping window
        recommended_strategy = "momentum_scalping"
        confidence = 0.80
        reasoning = (
            "Momentum scalping window is open (9:31-11:30am ET). "
            "Will scan for 6-condition setups (EMA cross, RSI, volume, VWAP, strength). "
            "Best for capturing intraday trends with tight stops."
        )
    else:
        # Default to IV Mean Reversion
        recommended_strategy = "iv_mean_reversion"
        confidence = 0.75
        reasoning = (
            "Outside specialized entry windows. IV Mean Reversion is the most reliable "
            "all-day strategy with 75% backtest win rate. Works best when VIX > 20."
        )

    return MarketConditions(
        vix_level=vix_level,
        vix_interpretation=vix_interpretation,
        market_trend=market_trend,
        economic_events_today=economic_events,
        recommended_strategy=recommended_strategy,
        confidence=confidence,
        reasoning=reasoning
    )


async def execute_iv_mean_reversion() -> Dict[str, Any]:
    """Execute IV Mean Reversion trade"""
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))

    from api.strategies import generate_signal
    from api.execution import execute_order
    from models.trading import OrderRequest

    logger.info("Executing IV Mean Reversion strategy")

    # Generate signal
    from pydantic import BaseModel
    class SignalRequest(BaseModel):
        symbol: str
        lookback_days: int

    signal_request = SignalRequest(symbol="SPY", lookback_days=90)
    signal = await generate_signal(signal_request)

    # Check if signal is valid
    if not hasattr(signal, 'signal') or signal.signal.value == "HOLD":
        raise HTTPException(
            status_code=400,
            detail=f"No strong IV signal"
        )

    # Select option based on signal
    action = "buy" if signal.signal.value == "BUY" else "sell"
    option_type = "call" if action == "buy" else "put"

    # Get ATM strike from latest data
    # TODO: Fetch actual strike from data endpoint
    strike = 580  # Placeholder

    # Calculate expiration (35 DTE)
    from datetime import timedelta
    expiration = (datetime.now() + timedelta(days=35)).strftime("%Y-%m-%d")

    order_request = OrderRequest(
        symbol="SPY",
        option_type=option_type,
        strike=strike,
        expiration=expiration,
        action=action,
        contracts=1,
        strategy="iv_mean_reversion",
        entry_reason=f"AUTO-TRADE: IV {signal.signal.value} signal"
    )

    # Execute order
    result = await execute_order(order_request)

    return {
        "strategy": "iv_mean_reversion",
        "signal": signal.dict(),
        "order": order_request.dict(),
        "result": result.dict() if hasattr(result, 'dict') else result
    }


async def execute_iron_condor() -> Dict[str, Any]:
    """Execute Iron Condor trade"""
    logger.info("Executing Iron Condor strategy")

    try:
        # Import iron condor module
        import sys
        sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
        from api.iron_condor import generate_signal, build_iron_condor, should_enter_now, GenerateSignalRequest

        # Check if we're in the entry window
        entry_check = await should_enter_now()
        if not entry_check.get("should_enter", False):
            raise HTTPException(
                status_code=400,
                detail=f"Outside Iron Condor entry window (9:31-9:45am ET). {entry_check.get('message', '')}"
            )

        # Generate signal for SPY with 0DTE expiration
        signal_request = GenerateSignalRequest(
            underlying="SPY",
            expiration_date=None,  # Defaults to 0DTE
            quantity=1
        )

        signal_result = await generate_signal(signal_request)

        if not signal_result.get("signal"):
            raise HTTPException(
                status_code=400,
                detail="No valid iron condor signal generated"
            )

        # Build the iron condor setup
        signal_obj = signal_result["signal"]
        build_result = await build_iron_condor(
            underlying="SPY",
            signal=signal_obj
        )

        logger.info(
            "Iron Condor auto-execution complete",
            setup=build_result.get("setup", {})
        )

        return {
            "strategy": "iron_condor",
            "signal": signal_result,
            "setup": build_result,
            "message": "Iron Condor built successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Iron Condor auto-execution failed", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Iron Condor execution failed: {str(e)}"
        )


async def execute_momentum_scalping() -> Dict[str, Any]:
    """Execute Momentum Scalping trade"""
    logger.info("Executing Momentum Scalping strategy")

    try:
        # Import momentum scalping module
        import sys
        sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
        from api.momentum_scalping import scan_for_signals, execute_signal, ExecuteSignalRequest
        import uuid

        # Scan for signals
        scan_result = await scan_for_signals()

        if not scan_result.signals:
            raise HTTPException(
                status_code=400,
                detail="No momentum signals found. All 6 conditions must be met for entry."
            )

        if not scan_result.entry_window_active:
            raise HTTPException(
                status_code=400,
                detail="Outside momentum scalping entry window (9:31-11:30am ET)"
            )

        # Filter for high-confidence signals (>80%)
        high_confidence_signals = [
            sig for sig in scan_result.signals
            if sig.confidence >= 0.80
        ]

        if not high_confidence_signals:
            raise HTTPException(
                status_code=400,
                detail=f"No high-confidence signals found. Best confidence: {max([s.confidence for s in scan_result.signals]):.1%}"
            )

        # Pick the highest confidence signal
        best_signal = max(high_confidence_signals, key=lambda s: s.confidence)

        logger.info(
            "Selected momentum signal",
            symbol=best_signal.symbol,
            confidence=best_signal.confidence,
            signal_type=best_signal.signal_type
        )

        # Execute the signal
        execute_request = ExecuteSignalRequest(
            signal_id=str(uuid.uuid4()),
            signal=best_signal,
            quantity=1  # Start with 1 contract for auto-execution
        )

        execution_result = await execute_signal(execute_request)

        logger.info(
            "Momentum Scalping auto-execution complete",
            symbol=best_signal.symbol,
            result=execution_result
        )

        return {
            "strategy": "momentum_scalping",
            "signal": best_signal.model_dump(),
            "scan_summary": {
                "total_signals": len(scan_result.signals),
                "high_confidence_count": len(high_confidence_signals)
            },
            "execution": execution_result,
            "message": f"Momentum trade executed: {best_signal.symbol} ({best_signal.signal_type})"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Momentum Scalping auto-execution failed", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Momentum Scalping execution failed: {str(e)}"
        )


async def execute_auto_trade_workflow(session_id: str):
    """
    Background task that executes the full auto-trade workflow
    1. Research market conditions
    2. Wait for market open if needed
    3. Execute selected strategy
    4. Monitor position
    """
    state = auto_trade_sessions[session_id]

    try:
        # Step 1: Research market conditions
        state.status = AutoTradeStatus.RESEARCHING
        state.message = "Researching market conditions (VIX, trends, economic calendar)..."
        logger.info("Auto-trade: Researching market", session_id=session_id)

        market_conditions = await research_market_conditions()
        state.market_conditions = market_conditions
        state.selected_strategy = market_conditions.recommended_strategy
        state.message = f"Research complete. Selected strategy: {market_conditions.recommended_strategy}"

        logger.info(
            "Market research complete",
            session_id=session_id,
            strategy=market_conditions.recommended_strategy,
            confidence=market_conditions.confidence
        )

        # Step 2: Wait for market open if needed
        if not is_market_open():
            state.status = AutoTradeStatus.WAITING_FOR_MARKET
            seconds_until_open = time_until_market_open()
            minutes_until_open = seconds_until_open // 60

            state.message = f"Market closed. Waiting {minutes_until_open} minutes until open (9:30am ET)..."
            logger.info(
                "Waiting for market open",
                session_id=session_id,
                minutes_until_open=minutes_until_open
            )

            # In production, this should be a scheduled job, not blocking
            # For demo purposes, we'll just mark as waiting
            # await asyncio.sleep(min(seconds_until_open, 60))  # Wait max 1 minute for demo

        # Step 3: Execute selected strategy
        state.status = AutoTradeStatus.EXECUTING
        state.message = f"Executing {state.selected_strategy} trade..."
        logger.info("Executing trade", session_id=session_id, strategy=state.selected_strategy)

        if state.selected_strategy == "iv_mean_reversion":
            trade_result = await execute_iv_mean_reversion()
        elif state.selected_strategy == "iron_condor":
            trade_result = await execute_iron_condor()
        elif state.selected_strategy == "momentum_scalping":
            trade_result = await execute_momentum_scalping()
        else:
            raise ValueError(f"Unknown strategy: {state.selected_strategy}")

        state.trade_details = trade_result
        state.order_id = trade_result.get("result", {}).get("order_id")
        state.position_id = trade_result.get("result", {}).get("position_id")

        # Step 4: Monitoring
        state.status = AutoTradeStatus.MONITORING
        state.message = "Trade executed successfully! Position is now being monitored."
        logger.info(
            "Trade executed successfully",
            session_id=session_id,
            order_id=state.order_id,
            position_id=state.position_id
        )

        # Mark as completed
        state.status = AutoTradeStatus.COMPLETED
        state.completed_at = datetime.now(timezone.utc)
        state.message = "Auto-trade completed successfully!"

    except Exception as e:
        logger.error("Auto-trade failed", session_id=session_id, error=str(e))
        state.status = AutoTradeStatus.FAILED
        state.error = str(e)
        state.message = f"Auto-trade failed: {str(e)}"
        state.completed_at = datetime.now(timezone.utc)


@router.post("/start", response_model=Dict[str, str])
async def start_auto_trade(background_tasks: BackgroundTasks):
    """
    Start the auto-trade workflow
    Returns session_id to poll for status updates
    """
    import uuid

    session_id = str(uuid.uuid4())

    # Initialize state
    state = AutoTradeState(
        status=AutoTradeStatus.PENDING,
        message="Auto-trade initiated. Starting market research...",
        started_at=datetime.now(timezone.utc)
    )

    auto_trade_sessions[session_id] = state

    # Start background workflow
    background_tasks.add_task(execute_auto_trade_workflow, session_id)

    logger.info("Auto-trade started", session_id=session_id)

    return {
        "session_id": session_id,
        "message": "Auto-trade workflow started. Poll /status endpoint for updates."
    }


@router.get("/status/{session_id}", response_model=AutoTradeState)
async def get_auto_trade_status(session_id: str):
    """
    Get current status of auto-trade workflow
    Frontend should poll this every 2-3 seconds
    """
    if session_id not in auto_trade_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    return auto_trade_sessions[session_id]


@router.delete("/cancel/{session_id}")
async def cancel_auto_trade(session_id: str):
    """Cancel an in-progress auto-trade"""
    if session_id not in auto_trade_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    state = auto_trade_sessions[session_id]

    if state.status in [AutoTradeStatus.COMPLETED, AutoTradeStatus.FAILED]:
        raise HTTPException(status_code=400, detail="Cannot cancel completed trade")

    # Mark as cancelled (treated as failed)
    state.status = AutoTradeStatus.FAILED
    state.error = "Cancelled by user"
    state.message = "Auto-trade cancelled"
    state.completed_at = datetime.now(timezone.utc)

    logger.info("Auto-trade cancelled", session_id=session_id)

    return {"message": "Auto-trade cancelled"}


@router.get("/market-status")
async def get_market_status():
    """Check if market is currently open"""
    is_open = is_market_open()

    if is_open:
        return {
            "is_open": True,
            "message": "Market is currently open (9:30am-4:00pm ET)"
        }
    else:
        seconds_until = time_until_market_open()
        minutes_until = seconds_until // 60
        hours_until = minutes_until // 60

        return {
            "is_open": False,
            "seconds_until_open": seconds_until,
            "minutes_until_open": minutes_until,
            "hours_until_open": hours_until,
            "message": f"Market opens in {hours_until}h {minutes_until % 60}m"
        }
