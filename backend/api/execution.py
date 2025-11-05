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
from alpaca.trading.requests import LimitOrderRequest, OrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce, OrderClass

from models.trading import Signal, RiskApproval, Execution, Portfolio, Position, SignalType
from models.strategies import OptionLeg, MultiLegOrder

logger = structlog.get_logger()

router = APIRouter(prefix="/api/execution", tags=["execution"])

# Initialize Alpaca Trading Client (PAPER TRADING ONLY)
ALPACA_API_KEY = os.getenv("ALPACA_API_KEY")
ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")

# CRITICAL: Validate paper trading API keys
if ALPACA_API_KEY and not ALPACA_API_KEY.startswith("PK"):
    logger.critical(
        "CRITICAL SAFETY WARNING: ALPACA_API_KEY should be a paper trading key (starts with 'PK')",
        current_prefix=ALPACA_API_KEY[:2]
    )

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


# ============================================================================
# Position Tracking Functions
# ============================================================================

async def create_position(
    symbol: str,
    strategy: str,
    position_type: str,
    quantity: int,
    entry_price: Decimal,
    entry_trade_id: Optional[int] = None
) -> Optional[int]:
    """
    Create a new open position in the database

    Args:
        symbol: Option symbol
        strategy: Strategy name
        position_type: 'long' or 'short'
        quantity: Number of contracts
        entry_price: Entry price per contract
        entry_trade_id: Trade ID from trades table

    Returns:
        Position ID if successful, None otherwise
    """
    try:
        if not supabase:
            logger.warning("Supabase not configured, skipping position tracking")
            return None

        data = {
            "symbol": symbol,
            "strategy": strategy,
            "position_type": position_type,
            "quantity": quantity,
            "entry_price": float(entry_price),
            "entry_trade_id": entry_trade_id,
            "current_price": float(entry_price),
            "unrealized_pnl": 0.0,
            "opened_at": datetime.utcnow().isoformat(),
            "status": "open"
        }

        response = supabase.table("positions").insert(data).execute()

        if response.data:
            position_id = response.data[0]['id']
            logger.info("Created position",
                       position_id=position_id,
                       symbol=symbol,
                       type=position_type,
                       quantity=quantity)
            return position_id

        return None

    except Exception as e:
        logger.error("Failed to create position", error=str(e))
        return None


async def create_multi_leg_position(
    multi_leg: MultiLegOrder,
    entry_trade_id: Optional[int] = None
) -> Optional[int]:
    """
    Create a multi-leg position in the database (iron condor, spreads, etc.)

    Args:
        multi_leg: MultiLegOrder with all legs configured
        entry_trade_id: Trade ID from trades table

    Returns:
        Position ID if successful, None otherwise
    """
    try:
        if not supabase:
            logger.warning("Supabase not configured, skipping position tracking")
            return None

        # Prepare legs data for JSONB storage
        legs_data = [
            {
                "symbol": leg.symbol,
                "side": leg.side,
                "option_type": leg.option_type,
                "strike": float(leg.strike),
                "quantity": leg.quantity,
                "entry_price": float(leg.limit_price) if leg.limit_price else None
            }
            for leg in multi_leg.legs
        ]

        # Use first leg symbol to extract underlying (e.g., "SPY251219C00600000" -> "SPY")
        first_symbol = multi_leg.legs[0].symbol
        underlying = first_symbol[:first_symbol.index(next(filter(str.isdigit, first_symbol)))]
        representative_symbol = f"{multi_leg.strategy_type}_{underlying}"

        # Prepare position data
        data = {
            "symbol": representative_symbol,
            "strategy": multi_leg.strategy_type,
            "position_type": "spread",  # Generic type for multi-leg positions
            "quantity": multi_leg.legs[0].quantity,  # Reference quantity (all legs same qty)
            "entry_price": float(multi_leg.net_credit) if multi_leg.net_credit else 0.0,
            "entry_trade_id": entry_trade_id,
            "current_price": float(multi_leg.net_credit) if multi_leg.net_credit else 0.0,
            "unrealized_pnl": 0.0,
            "opened_at": datetime.utcnow().isoformat(),
            "status": "open",
            # Multi-leg specific fields
            "legs": legs_data,
            "net_credit": float(multi_leg.net_credit) if multi_leg.net_credit else None,
            "max_loss": float(multi_leg.max_loss) if multi_leg.max_loss else None,
            "spread_width": 5.0  # Default for SPY/QQQ (TODO: make configurable)
        }

        response = supabase.table("positions").insert(data).execute()

        if response.data:
            position_id = response.data[0]['id']
            logger.info("Created multi-leg position",
                       position_id=position_id,
                       strategy=multi_leg.strategy_type,
                       legs=len(multi_leg.legs),
                       underlying=underlying)
            return position_id

        return None

    except Exception as e:
        logger.error("Failed to create multi-leg position", error=str(e))
        return None


async def get_open_positions() -> list[Position]:
    """
    Fetch all open positions from database

    Returns:
        List of Position objects with status='open'
    """
    try:
        if not supabase:
            return []

        response = supabase.table("positions")\
            .select("*")\
            .eq("status", "open")\
            .execute()

        if not response.data:
            return []

        positions = []
        for row in response.data:
            position = Position(
                id=row['id'],
                symbol=row['symbol'],
                strategy=row['strategy'],
                position_type=row['position_type'],
                quantity=row['quantity'],
                entry_price=Decimal(str(row['entry_price'])),
                entry_trade_id=row.get('entry_trade_id'),
                current_price=Decimal(str(row['current_price'])) if row.get('current_price') else None,
                unrealized_pnl=Decimal(str(row['unrealized_pnl'])) if row.get('unrealized_pnl') else None,
                opened_at=datetime.fromisoformat(row['opened_at'].replace('Z', '+00:00')),
                status=row['status']
            )
            positions.append(position)

        return positions

    except Exception as e:
        logger.error("Failed to fetch open positions", error=str(e))
        return []


async def update_position_status(
    position_id: int,
    status: str,
    exit_trade_id: Optional[int] = None,
    closed_at: Optional[datetime] = None,
    exit_reason: Optional[str] = None
) -> bool:
    """
    Update position status (close position)

    Args:
        position_id: Position ID to update
        status: New status ('open' or 'closed')
        exit_trade_id: Trade ID for exit
        closed_at: Timestamp when closed
        exit_reason: Reason for exit

    Returns:
        True if successful, False otherwise
    """
    try:
        if not supabase:
            return False

        data = {"status": status}

        if exit_trade_id:
            data["exit_trade_id"] = exit_trade_id

        if closed_at:
            data["closed_at"] = closed_at.isoformat()

        if exit_reason:
            data["exit_reason"] = exit_reason

        supabase.table("positions")\
            .update(data)\
            .eq("id", position_id)\
            .execute()

        logger.info("Updated position status",
                   position_id=position_id,
                   status=status,
                   reason=exit_reason)

        return True

    except Exception as e:
        logger.error("Failed to update position status",
                    position_id=position_id,
                    error=str(e))
        return False


async def log_trade_to_supabase(execution: Execution, signal: Signal) -> Optional[int]:
    """
    Log trade execution to Supabase

    Args:
        execution: Execution details
        signal: Trading signal

    Returns:
        Trade ID if successful, None otherwise
    """
    try:
        if not supabase:
            logger.warning("Supabase not configured, skipping trade log")
            return None

        data = {
            "timestamp": execution.timestamp.isoformat(),
            "symbol": execution.symbol,
            "strategy": signal.strategy,
            "signal_type": signal.signal.value,
            "entry_price": float(execution.entry_price),
            "exit_price": float(execution.exit_price) if execution.exit_price else None,
            "quantity": execution.quantity,
            "pnl": float(execution.pnl) if execution.pnl else None,
            "commission": float(execution.commission),
            "slippage": float(execution.slippage),
            "reasoning": signal.reasoning
        }

        response = supabase.table("trades").insert(data).execute()

        if response.data:
            trade_id = response.data[0]['id']
            logger.info("Logged trade to Supabase",
                       trade_id=trade_id,
                       symbol=execution.symbol,
                       signal=signal.signal.value)
            return trade_id

        return None

    except Exception as e:
        logger.error("Failed to log trade", error=str(e))
        return None


async def log_multi_leg_trade_to_supabase(
    execution: Execution,
    multi_leg: MultiLegOrder
) -> Optional[int]:
    """
    Log multi-leg trade execution to Supabase

    Args:
        execution: Combined execution record
        multi_leg: Multi-leg order details

    Returns:
        Trade ID if successful, None otherwise
    """
    try:
        if not supabase:
            logger.warning("Supabase not configured, skipping trade log")
            return None

        data = {
            "timestamp": execution.timestamp.isoformat(),
            "symbol": execution.symbol,  # e.g., "iron_condor_SPY"
            "strategy": multi_leg.strategy_type,
            "signal_type": "open_multi_leg",  # Custom signal type for spreads
            "entry_price": float(execution.entry_price),  # Net credit/debit per contract
            "exit_price": None,
            "quantity": execution.quantity,  # Reference quantity
            "pnl": None,
            "commission": float(execution.commission),
            "slippage": float(execution.slippage),
            "reasoning": f"{multi_leg.strategy_type} with {len(multi_leg.legs)} legs"
        }

        response = supabase.table("trades").insert(data).execute()

        if response.data:
            trade_id = response.data[0]['id']
            logger.info("Logged multi-leg trade to Supabase",
                       trade_id=trade_id,
                       strategy=multi_leg.strategy_type,
                       legs=len(multi_leg.legs))
            return trade_id

        return None

    except Exception as e:
        logger.error("Failed to log multi-leg trade", error=str(e))
        return None


def calculate_slippage(expected_price: Decimal, actual_price: Decimal) -> Decimal:
    """
    Calculate slippage as percentage difference

    Slippage % = (Actual - Expected) / Expected
    """
    if expected_price == 0:
        return Decimal('0')

    slippage = (actual_price - expected_price) / expected_price
    return slippage


def parse_option_symbol(symbol: str) -> dict:
    """
    Parse OCC option symbol format: AAPL251219C00150000

    Returns:
        dict with underlying, expiration, option_type, strike
    """
    try:
        # Extract components from OCC format
        underlying = symbol[:symbol.index(str(next(filter(str.isdigit, symbol))))]
        date_start = len(underlying)
        expiration_str = symbol[date_start:date_start+6]
        option_type = symbol[date_start+6]
        strike_str = symbol[date_start+7:]

        # Parse expiration (YYMMDD)
        from datetime import datetime
        year = 2000 + int(expiration_str[:2])
        month = int(expiration_str[2:4])
        day = int(expiration_str[4:6])
        expiration = datetime(year, month, day)

        # Parse strike (8 digits, divide by 1000)
        strike = Decimal(strike_str) / 1000

        return {
            'underlying': underlying,
            'expiration': expiration,
            'option_type': option_type,
            'strike': strike
        }
    except Exception as e:
        logger.error("Failed to parse option symbol", symbol=symbol, error=str(e))
        return {}


async def get_latest_tick(symbol: str):
    """
    Get latest option tick from database or fetch from Alpaca

    Args:
        symbol: Option symbol

    Returns:
        OptionTick with latest market data
    """
    try:
        if not supabase:
            return None

        # Try to get from database first
        response = supabase.table("option_ticks")\
            .select("*")\
            .eq("symbol", symbol)\
            .order("timestamp", desc=True)\
            .limit(1)\
            .execute()

        if response.data:
            row = response.data[0]
            from models.trading import OptionTick
            parsed = parse_option_symbol(symbol)

            tick = OptionTick(
                symbol=symbol,
                underlying_price=Decimal(str(row['underlying_price'])),
                strike=Decimal(str(row['strike'])),
                expiration=parsed.get('expiration', datetime.utcnow()),
                bid=Decimal(str(row['bid'])),
                ask=Decimal(str(row['ask'])),
                delta=Decimal(str(row.get('delta', 0))),
                gamma=Decimal(str(row.get('gamma', 0))),
                theta=Decimal(str(row.get('theta', 0))),
                vega=Decimal(str(row.get('vega', 0))),
                iv=Decimal(str(row.get('iv', 0))),
                timestamp=datetime.fromisoformat(row['timestamp'].replace('Z', '+00:00'))
            )
            return tick

        return None

    except Exception as e:
        logger.error("Failed to get latest tick", symbol=symbol, error=str(e))
        return None


async def is_earnings_blackout(symbol: str) -> bool:
    """
    Check if underlying has earnings within 2 days

    TODO: Integrate with earnings calendar API
    For now, returns False (no blackout)

    Args:
        symbol: Option symbol

    Returns:
        True if earnings within 2 days, False otherwise
    """
    # TODO: Implement earnings check using a calendar API
    # For now, assume no earnings blackout
    return False


async def check_exit_conditions(position: Position) -> Optional[str]:
    """
    Check if position should be exited based on P&L or DTE

    Args:
        position: Position to evaluate

    Returns:
        Exit reason if should exit, None otherwise
    """
    try:
        # Get current price
        latest_tick = await get_latest_tick(position.symbol)
        if not latest_tick:
            logger.warning("No tick data for position", symbol=position.symbol)
            return None

        current_price = (latest_tick.bid + latest_tick.ask) / 2

        # Calculate P&L percentage
        if position.position_type == "long":
            pnl_pct = (current_price - position.entry_price) / position.entry_price
        else:  # short
            pnl_pct = (position.entry_price - current_price) / position.entry_price

        # Exit condition: 50% profit target
        if pnl_pct >= Decimal('0.50'):
            return "50% profit target reached"

        # Exit condition: 75% stop loss
        if pnl_pct <= Decimal('-0.75'):
            return "75% stop loss hit"

        # Exit condition: 21 DTE threshold
        parsed = parse_option_symbol(position.symbol)
        if parsed:
            expiration = parsed.get('expiration')
            if expiration:
                dte = (expiration - datetime.now()).days
                if dte <= 21:
                    return "21 DTE threshold reached"

        # Exit condition: Earnings blackout
        if await is_earnings_blackout(position.symbol):
            return "Earnings within 2 days"

        return None

    except Exception as e:
        logger.error("Failed to check exit conditions",
                    position_id=position.id,
                    error=str(e))
        return None


async def close_position(position: Position) -> OrderResponse:
    """
    Close an open position by placing opposite order

    Args:
        position: Position to close

    Returns:
        OrderResponse with close execution details
    """
    try:
        # Determine order side for closing
        if position.position_type == "long":
            side = OrderSide.SELL  # Sell to close long
            signal_type = SignalType.CLOSE_LONG
        else:
            side = OrderSide.BUY   # Buy to close short
            signal_type = SignalType.CLOSE_SHORT

        # Get current price for limit order
        latest_tick = await get_latest_tick(position.symbol)
        if not latest_tick:
            return OrderResponse(
                success=False,
                message=f"Cannot get current price for {position.symbol}"
            )

        limit_price = latest_tick.ask if side == OrderSide.BUY else latest_tick.bid

        # Create close signal
        close_signal = Signal(
            symbol=position.symbol,
            signal=signal_type,
            strategy=position.strategy,
            confidence=1.0,
            entry_price=limit_price,
            stop_loss=Decimal('0'),
            take_profit=Decimal('0'),
            reasoning="Automated position exit",
            timestamp=datetime.utcnow()
        )

        # Execute close order
        result = await place_limit_order(close_signal, position.quantity)

        if result.success:
            # Calculate P&L
            if position.position_type == "long":
                pnl = (limit_price - position.entry_price) * position.quantity * 100
            else:  # short
                pnl = (position.entry_price - limit_price) * position.quantity * 100

            # Get trade_id from result
            trade_id = await log_trade_to_supabase(result.execution, close_signal)

            # Mark position as closed
            await update_position_status(
                position.id,
                status='closed',
                exit_trade_id=trade_id,
                closed_at=datetime.utcnow(),
                exit_reason="Automated exit"
            )

            logger.info("Position closed",
                       position_id=position.id,
                       symbol=position.symbol,
                       pnl=float(pnl))

        return result

    except Exception as e:
        logger.error("Failed to close position",
                    position_id=position.id,
                    error=str(e))
        return OrderResponse(
            success=False,
            message=f"Failed to close position: {str(e)}"
        )


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

        # Log to Supabase and get trade ID
        trade_id = await log_trade_to_supabase(execution, signal)

        # Track position if opening (BUY or SELL)
        if signal.signal in [SignalType.BUY, SignalType.SELL]:
            position_type = "long" if signal.signal == SignalType.BUY else "short"
            await create_position(
                symbol=signal.symbol,
                strategy=signal.strategy,
                position_type=position_type,
                quantity=quantity,
                entry_price=actual_price,
                entry_trade_id=trade_id
            )
            logger.info("Position opened",
                       symbol=signal.symbol,
                       type=position_type,
                       quantity=quantity)

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


async def place_multi_leg_order(multi_leg: MultiLegOrder) -> OrderResponse:
    """
    Place a multi-leg options order (spread, condor, butterfly, etc.)

    Args:
        multi_leg: MultiLegOrder with all legs configured

    Returns:
        OrderResponse with execution details
    """
    try:
        if not trading_client:
            raise HTTPException(status_code=500, detail="Trading client not initialized")

        # Alpaca supports multi-leg orders via OrderClass.BRACKET
        # For iron condors and spreads, we'll submit each leg individually but link them
        # TODO: Investigate if Alpaca has native multi-leg order support

        # For now, submit legs sequentially
        all_legs_filled = []
        total_cost = Decimal('0')

        for leg in multi_leg.legs:
            # Determine order side
            side = OrderSide.BUY if leg.side == "buy" else OrderSide.SELL

            # Create limit order for this leg
            limit_price = float(leg.limit_price) if leg.limit_price else None

            if not limit_price:
                # Use market mid if no limit specified
                # In production, fetch current quotes
                raise ValueError(f"Limit price required for leg {leg.symbol}")

            order_request = LimitOrderRequest(
                symbol=leg.symbol,
                qty=leg.quantity,
                side=side,
                time_in_force=TimeInForce.DAY,
                limit_price=limit_price
            )

            # Submit order
            order = trading_client.submit_order(order_request)

            logger.info("Multi-leg order leg submitted",
                       strategy=multi_leg.strategy_type,
                       symbol=leg.symbol,
                       side=side.value,
                       quantity=leg.quantity,
                       order_id=order.id)

            all_legs_filled.append({
                "symbol": leg.symbol,
                "side": leg.side,
                "quantity": leg.quantity,
                "price": leg.limit_price,
                "order_id": str(order.id)
            })

            # Calculate cost (credit vs debit)
            if leg.side == "sell":
                total_cost -= leg.limit_price * leg.quantity * 100
            else:  # buy
                total_cost += leg.limit_price * leg.quantity * 100

        # Calculate commission: $0.65 per contract per leg
        total_contracts = sum(leg.quantity for leg in multi_leg.legs)
        commission = Decimal('0.65') * total_contracts

        # Create combined execution record
        # Use first leg symbol as representative
        first_leg = multi_leg.legs[0]
        execution = Execution(
            symbol=f"{multi_leg.strategy_type}_{first_leg.symbol[:3]}",  # e.g., "iron_condor_SPY"
            quantity=first_leg.quantity,  # Reference quantity
            entry_price=abs(total_cost / (first_leg.quantity * 100)),  # Per-contract net cost
            commission=commission,
            slippage=Decimal('0'),  # TODO: Calculate from actual fills
            timestamp=datetime.utcnow()
        )

        # Log multi-leg trade to Supabase
        trade_id = await log_multi_leg_trade_to_supabase(execution, multi_leg)

        # Create multi-leg position in database
        if trade_id:
            position_id = await create_multi_leg_position(multi_leg, entry_trade_id=trade_id)
            if position_id:
                logger.info("Multi-leg position tracked in database",
                           position_id=position_id,
                           trade_id=trade_id,
                           strategy=multi_leg.strategy_type)
            else:
                logger.warning("Failed to create position record for multi-leg order")
        else:
            logger.warning("Failed to log multi-leg trade to database")

        return OrderResponse(
            success=True,
            execution=execution,
            alpaca_order_id=",".join([leg["order_id"] for leg in all_legs_filled]),
            message=f"Multi-leg {multi_leg.strategy_type} placed: {len(multi_leg.legs)} legs"
        )

    except Exception as e:
        logger.error("Failed to place multi-leg order",
                    strategy=multi_leg.strategy_type,
                    error=str(e))
        return OrderResponse(
            success=False,
            message=f"Multi-leg order failed: {str(e)}"
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


@router.post("/order/multi-leg")
async def execute_multi_leg_order(multi_leg: MultiLegOrder) -> OrderResponse:
    """
    Execute a multi-leg options order (spread, condor, butterfly, etc.)

    Args:
        multi_leg: MultiLegOrder with all legs configured

    Returns:
        OrderResponse with execution details
    """
    try:
        response = await place_multi_leg_order(multi_leg)
        return response

    except Exception as e:
        logger.error("Error in execute_multi_leg_order", error=str(e))
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


@router.get("/trades")
async def get_trades(limit: int = 50):
    """
    Get recent trades from database

    Args:
        limit: Maximum number of trades to return (default 50)

    Returns:
        List of trades ordered by timestamp descending
    """
    try:
        if not supabase:
            logger.warning("Supabase not configured, returning empty trades")
            return []

        response = supabase.table("trades").select("*").order("timestamp", desc=True).limit(limit).execute()
        return response.data

    except Exception as e:
        logger.error("Error fetching trades", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to fetch trades: {str(e)}")


@router.get("/trades/{trade_id}")
async def get_trade_by_id(trade_id: int):
    """
    Get specific trade by ID

    Args:
        trade_id: Trade ID from database

    Returns:
        Trade details
    """
    try:
        if not supabase:
            raise HTTPException(status_code=503, detail="Database not configured")

        response = supabase.table("trades").select("*").eq("id", trade_id).execute()

        if not response.data:
            raise HTTPException(status_code=404, detail=f"Trade {trade_id} not found")

        return response.data[0]

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching trade", trade_id=trade_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to fetch trade: {str(e)}")


@router.get("/performance")
async def get_performance():
    """
    Calculate performance metrics from trades

    Returns:
        Performance metrics: total trades, win rate, PnL, Sharpe ratio, etc.
    """
    try:
        if not supabase:
            logger.warning("Supabase not configured, returning empty performance")
            return {
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "win_rate": 0.0,
                "total_pnl": 0.0,
                "sharpe_ratio": 0.0,
                "max_drawdown": 0.0
            }

        # Fetch all trades
        response = supabase.table("trades").select("pnl, exit_price").execute()
        trades = response.data

        if not trades:
            return {
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "win_rate": 0.0,
                "total_pnl": 0.0,
                "sharpe_ratio": 0.0,
                "max_drawdown": 0.0
            }

        # Calculate metrics
        closed_trades = [t for t in trades if t.get("exit_price") is not None]
        total_trades = len(closed_trades)

        if total_trades == 0:
            return {
                "total_trades": len(trades),
                "winning_trades": 0,
                "losing_trades": 0,
                "win_rate": 0.0,
                "total_pnl": 0.0,
                "sharpe_ratio": 0.0,
                "max_drawdown": 0.0
            }

        winning_trades = sum(1 for t in closed_trades if t.get("pnl", 0) > 0)
        losing_trades = total_trades - winning_trades
        win_rate = winning_trades / total_trades if total_trades > 0 else 0.0

        total_pnl = sum(float(t.get("pnl", 0)) for t in closed_trades)

        # Simple Sharpe calculation (assuming daily returns, 252 trading days)
        pnls = [float(t.get("pnl", 0)) for t in closed_trades]
        if len(pnls) > 1:
            import math
            mean_pnl = sum(pnls) / len(pnls)
            variance = sum((p - mean_pnl) ** 2 for p in pnls) / (len(pnls) - 1)
            std_dev = math.sqrt(variance)
            sharpe_ratio = (mean_pnl / std_dev * math.sqrt(252)) if std_dev > 0 else 0.0
        else:
            sharpe_ratio = 0.0

        # Simple max drawdown (cumulative PnL)
        cumulative_pnl = 0
        max_pnl = 0
        max_drawdown = 0
        for pnl in pnls:
            cumulative_pnl += pnl
            max_pnl = max(max_pnl, cumulative_pnl)
            drawdown = max_pnl - cumulative_pnl
            max_drawdown = max(max_drawdown, drawdown)

        return {
            "total_trades": total_trades,
            "winning_trades": winning_trades,
            "losing_trades": losing_trades,
            "win_rate": round(win_rate, 4),
            "total_pnl": round(total_pnl, 2),
            "sharpe_ratio": round(sharpe_ratio, 2),
            "max_drawdown": round(max_drawdown, 2)
        }

    except Exception as e:
        logger.error("Error calculating performance", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to calculate performance: {str(e)}")


@router.get("/positions")
async def get_positions(status: str = "open", limit: int = 50):
    """
    Get positions from database

    Args:
        status: Filter by status ('open', 'closed', or 'all')
        limit: Maximum number of positions to return (default 50)

    Returns:
        List of positions ordered by opened_at descending
    """
    try:
        if not supabase:
            logger.warning("Supabase not configured, returning empty positions")
            return []

        query = supabase.table("positions").select("*")

        if status != "all":
            query = query.eq("status", status)

        response = query.order("opened_at", desc=True).limit(limit).execute()
        return response.data

    except Exception as e:
        logger.error("Error fetching positions", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to fetch positions: {str(e)}")


@router.get("/positions/{position_id}")
async def get_position_by_id(position_id: int):
    """
    Get specific position by ID

    Args:
        position_id: Position ID from database

    Returns:
        Position details with entry/exit trades
    """
    try:
        if not supabase:
            raise HTTPException(status_code=503, detail="Database not configured")

        response = supabase.table("positions").select("*").eq("id", position_id).execute()

        if not response.data:
            raise HTTPException(status_code=404, detail=f"Position {position_id} not found")

        return response.data[0]

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching position", position_id=position_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to fetch position: {str(e)}")


@router.get("/health")
async def health_check():
    """Check if execution service is operational"""
    return {
        "status": "ok",
        "trading_client_configured": bool(trading_client),
        "supabase_configured": bool(supabase),
        "paper_trading": True  # Always paper trading
    }

