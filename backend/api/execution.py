"""
Execution Service - Alpaca Order Placement

Places limit orders, tracks slippage, logs trades to Supabase.
Paper trading only.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from decimal import Decimal
from datetime import datetime
from typing import Optional
import os
import structlog
from supabase import create_client, Client
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import LimitOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce

from ..models.trading import Signal, RiskApproval, Execution, Portfolio

logger = structlog.get_logger()

router = APIRouter(prefix="/api/execution", tags=["execution"])

# Initialize Alpaca Trading Client (PAPER TRADING ONLY)
ALPACA_API_KEY = os.getenv("ALPACA_API_KEY")
ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")

# Initialize Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

trading_client: Optional[TradingClient] = None
supabase: Optional[Client] = None

try:
    if ALPACA_API_KEY and ALPACA_SECRET_KEY:
        # paper=True ensures we only use paper trading
        trading_client = TradingClient(ALPACA_API_KEY, ALPACA_SECRET_KEY, paper=True)
        logger.info("Alpaca trading client initialized (PAPER TRADING)")
    
    if SUPABASE_URL and SUPABASE_KEY:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        logger.info("Supabase client initialized")
except Exception as e:
    logger.error("Failed to initialize clients", error=str(e))


class OrderRequest(BaseModel):
    """Request to place an order"""
    signal: Signal
    approval: RiskApproval


class OrderResponse(BaseModel):
    """Response from order placement"""
    success: bool
    execution: Optional[Execution] = None
    alpaca_order_id: Optional[str] = None
    message: str


class PortfolioResponse(BaseModel):
    """Response with current portfolio state"""
    portfolio: Portfolio


async def log_trade_to_supabase(execution: Execution):
    """Log trade execution to Supabase"""
    try:
        if not supabase:
            logger.warning("Supabase not configured, skipping trade log")
            return
        
        data = {
            "timestamp": execution.timestamp.isoformat(),
            "symbol": execution.symbol,
            "strategy": "iv_mean_reversion",  # TODO: Get from signal
            "signal_type": "buy",  # TODO: Get from signal
            "entry_price": float(execution.entry_price),
            "exit_price": float(execution.exit_price) if execution.exit_price else None,
            "quantity": execution.quantity,
            "pnl": float(execution.pnl) if execution.pnl else None,
            "commission": float(execution.commission),
            "slippage": float(execution.slippage),
            "reasoning": ""  # TODO: Add signal reasoning
        }
        
        supabase.table("trades").insert(data).execute()
        logger.info("Logged trade to Supabase", symbol=execution.symbol)
        
    except Exception as e:
        logger.error("Failed to log trade", error=str(e))


def calculate_slippage(expected_price: Decimal, actual_price: Decimal) -> Decimal:
    """
    Calculate slippage as percentage difference
    
    Slippage % = (Actual - Expected) / Expected
    """
    if expected_price == 0:
        return Decimal('0')
    
    slippage = (actual_price - expected_price) / expected_price
    return slippage


async def place_limit_order(signal: Signal, quantity: int) -> OrderResponse:
    """
    Place a limit order with Alpaca
    
    Args:
        signal: Trading signal with entry price
        quantity: Number of contracts to trade
    
    Returns:
        OrderResponse with execution details
    """
    try:
        if not trading_client:
            raise HTTPException(status_code=500, detail="Trading client not initialized")
        
        # Determine order side
        side = OrderSide.BUY if signal.signal.value == "buy" else OrderSide.SELL
        
        # Create limit order request
        limit_price = float(signal.entry_price)
        
        order_request = LimitOrderRequest(
            symbol=signal.symbol,
            qty=quantity,
            side=side,
            time_in_force=TimeInForce.DAY,  # Cancel at end of day if not filled
            limit_price=limit_price
        )
        
        # Submit order to Alpaca
        order = trading_client.submit_order(order_request)
        
        logger.info("Order submitted to Alpaca",
                   symbol=signal.symbol,
                   side=side.value,
                   quantity=quantity,
                   limit_price=limit_price,
                   order_id=order.id)
        
        # For now, assume order fills at limit price (in reality, need to wait for fill)
        # TODO: Implement order status monitoring
        actual_price = signal.entry_price
        
        # Calculate commission: $0.65 per contract
        commission = Decimal('0.65') * quantity
        
        # Calculate slippage (for paper trading, assume minimal slippage)
        # In production, get actual fill price and calculate
        slippage = calculate_slippage(signal.entry_price, actual_price)
        
        # Create execution record
        execution = Execution(
            symbol=signal.symbol,
            quantity=quantity,
            entry_price=actual_price,
            commission=commission,
            slippage=slippage,
            timestamp=datetime.utcnow()
        )
        
        # Log to Supabase
        await log_trade_to_supabase(execution)
        
        return OrderResponse(
            success=True,
            execution=execution,
            alpaca_order_id=str(order.id),
            message=f"Order placed: {side.value} {quantity} contracts at ${limit_price}"
        )
        
    except Exception as e:
        logger.error("Failed to place order", symbol=signal.symbol, error=str(e))
        return OrderResponse(
            success=False,
            message=f"Order failed: {str(e)}"
        )


async def get_current_portfolio() -> Portfolio:
    """
    Fetch current portfolio state from Alpaca
    
    Returns:
        Portfolio with current balance, positions, and stats
    """
    try:
        if not trading_client:
            logger.warning("Trading client not configured, returning mock portfolio")
            return Portfolio(
                balance=Decimal('10000.00'),
                daily_pnl=Decimal('0.00'),
                win_rate=0.0,
                consecutive_losses=0,
                delta=Decimal('0'),
                theta=Decimal('0'),
                active_positions=0,
                total_trades=0
            )
        
        # Get account info
        account = trading_client.get_account()
        
        # Get positions
        positions = trading_client.get_all_positions()
        
        # Calculate daily P&L
        daily_pnl = Decimal(str(account.equity)) - Decimal(str(account.last_equity))
        
        # Get trade statistics from Supabase
        win_rate = 0.0
        consecutive_losses = 0
        total_trades = 0
        
        if supabase:
            try:
                # Get recent trades
                response = supabase.table("trades")\
                    .select("pnl")\
                    .not_.is_("exit_price", "null")\
                    .order("timestamp", desc=True)\
                    .limit(100)\
                    .execute()
                
                if response.data:
                    pnls = [Decimal(str(row['pnl'])) for row in response.data]
                    total_trades = len(pnls)
                    wins = sum(1 for p in pnls if p > 0)
                    win_rate = wins / total_trades if total_trades > 0 else 0.0
                    
                    # Count consecutive losses
                    for pnl in pnls:
                        if pnl < 0:
                            consecutive_losses += 1
                        else:
                            break
            except Exception as e:
                logger.error("Failed to fetch trade stats", error=str(e))
        
        # Create portfolio
        portfolio = Portfolio(
            balance=Decimal(str(account.equity)),
            daily_pnl=daily_pnl,
            win_rate=win_rate,
            consecutive_losses=consecutive_losses,
            delta=Decimal('0'),  # TODO: Aggregate delta from positions
            theta=Decimal('0'),  # TODO: Aggregate theta from positions
            active_positions=len(positions),
            total_trades=total_trades
        )
        
        logger.info("Fetched portfolio",
                   balance=float(portfolio.balance),
                   daily_pnl=float(daily_pnl),
                   positions=len(positions))
        
        return portfolio
        
    except Exception as e:
        logger.error("Failed to fetch portfolio", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/order")
async def execute_order(request: OrderRequest) -> OrderResponse:
    """
    Execute a trade based on signal and risk approval
    
    Args:
        request: Contains signal and risk approval
    
    Returns:
        OrderResponse with execution details
    """
    try:
        # Check if trade is approved
        if not request.approval.approved:
            return OrderResponse(
                success=False,
                message=f"Trade not approved: {request.approval.reasoning}"
            )
        
        # Place limit order
        response = await place_limit_order(request.signal, request.approval.position_size)
        
        return response
        
    except Exception as e:
        logger.error("Error in execute_order", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/portfolio")
async def get_portfolio() -> PortfolioResponse:
    """
    Get current portfolio state
    
    Returns:
        Portfolio with balance, positions, and statistics
    """
    try:
        portfolio = await get_current_portfolio()
        return PortfolioResponse(portfolio=portfolio)
    except Exception as e:
        logger.error("Error in get_portfolio", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """Check if execution service is operational"""
    return {
        "status": "ok",
        "trading_client_configured": bool(trading_client),
        "supabase_configured": bool(supabase),
        "paper_trading": True  # Always paper trading
    }

