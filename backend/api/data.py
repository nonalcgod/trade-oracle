"""
Data Service - Alpaca WebSocket integration with Greeks calculation

Streams real-time option data from Alpaca and calculates Greeks.
Logs all ticks to Supabase for historical analysis.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from decimal import Decimal
from datetime import datetime
import os
from typing import Optional
import asyncio
from alpaca.data.live import StockDataStream
from alpaca.data.historical import OptionHistoricalDataClient
from alpaca.data.requests import OptionLatestQuoteRequest
from supabase import create_client, Client
import structlog

from ..models.trading import OptionTick
from ..utils.greeks import calculate_all_greeks

logger = structlog.get_logger()

router = APIRouter(prefix="/api/data", tags=["data"])

# Initialize Alpaca clients
ALPACA_API_KEY = os.getenv("ALPACA_API_KEY")
ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")
ALPACA_BASE_URL = os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")

# Initialize Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

if not all([ALPACA_API_KEY, ALPACA_SECRET_KEY, SUPABASE_URL, SUPABASE_KEY]):
    logger.warning("Missing environment variables for data service")

supabase: Optional[Client] = None
option_client: Optional[OptionHistoricalDataClient] = None

try:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    option_client = OptionHistoricalDataClient(ALPACA_API_KEY, ALPACA_SECRET_KEY)
except Exception as e:
    logger.error("Failed to initialize clients", error=str(e))


class StreamRequest(BaseModel):
    """Request to start streaming option data"""
    symbols: list[str]  # List of option symbols to stream


class LatestDataResponse(BaseModel):
    """Response with latest option data"""
    tick: Optional[OptionTick] = None
    error: Optional[str] = None


async def log_tick_to_supabase(tick: OptionTick):
    """Log option tick to Supabase for historical analysis"""
    try:
        if supabase:
            data = {
                "timestamp": tick.timestamp.isoformat(),
                "symbol": tick.symbol,
                "underlying_price": float(tick.underlying_price),
                "strike": float(tick.strike),
                "bid": float(tick.bid),
                "ask": float(tick.ask),
                "delta": float(tick.delta),
                "gamma": float(tick.gamma),
                "theta": float(tick.theta),
                "vega": float(tick.vega),
                "iv": float(tick.iv)
            }
            supabase.table("option_ticks").insert(data).execute()
            logger.debug("Logged tick to Supabase", symbol=tick.symbol)
    except Exception as e:
        logger.error("Failed to log tick to Supabase", error=str(e), symbol=tick.symbol)


def parse_option_symbol(symbol: str) -> dict:
    """
    Parse option symbol to extract components
    Format: SPY250117C00450000
    - SPY: underlying
    - 250117: expiration YYMMDD
    - C/P: call or put
    - 00450000: strike * 1000
    """
    try:
        underlying = symbol[:3]  # First 3 chars
        exp_date_str = symbol[3:9]  # YYMMDD
        option_type = symbol[9]  # C or P
        strike_str = symbol[10:]  # Strike price * 1000
        
        # Parse expiration
        exp_year = 2000 + int(exp_date_str[0:2])
        exp_month = int(exp_date_str[2:4])
        exp_day = int(exp_date_str[4:6])
        expiration = datetime(exp_year, exp_month, exp_day, 16, 0, 0)  # Market close
        
        # Parse strike
        strike = Decimal(strike_str) / Decimal('1000')
        
        is_call = option_type == 'C'
        
        return {
            'underlying': underlying,
            'expiration': expiration,
            'strike': strike,
            'is_call': is_call
        }
    except Exception as e:
        logger.error("Failed to parse option symbol", symbol=symbol, error=str(e))
        raise ValueError(f"Invalid option symbol format: {symbol}")


async def get_underlying_price(underlying: str) -> Decimal:
    """Fetch current price of underlying stock"""
    # TODO: Implement real-time price fetching from Alpaca
    # For now, return a placeholder
    # In production, use Alpaca Stock API
    return Decimal('450.00')  # Placeholder


async def fetch_option_data_with_greeks(symbol: str) -> OptionTick:
    """
    Fetch latest option quote and calculate Greeks
    
    Args:
        symbol: Option symbol (e.g., SPY250117C00450000)
    
    Returns:
        OptionTick with market data and calculated Greeks
    """
    try:
        # Parse option symbol
        parsed = parse_option_symbol(symbol)
        
        # Fetch latest quote from Alpaca
        if not option_client:
            raise HTTPException(status_code=500, detail="Option client not initialized")
        
        request = OptionLatestQuoteRequest(symbol_or_symbols=symbol)
        quotes = option_client.get_option_latest_quote(request)
        
        if symbol not in quotes:
            raise HTTPException(status_code=404, detail=f"No data found for {symbol}")
        
        quote = quotes[symbol]
        
        # Get underlying price
        underlying_price = await get_underlying_price(parsed['underlying'])
        
        # Calculate mid price
        bid = Decimal(str(quote.bid_price)) if quote.bid_price else Decimal('0')
        ask = Decimal(str(quote.ask_price)) if quote.ask_price else Decimal('0')
        mid_price = (bid + ask) / 2
        
        # Calculate Greeks
        greeks = calculate_all_greeks(
            underlying_price=underlying_price,
            strike=parsed['strike'],
            expiration=parsed['expiration'],
            option_price=mid_price,
            is_call=parsed['is_call']
        )
        
        # Create OptionTick
        tick = OptionTick(
            symbol=symbol,
            underlying_price=underlying_price,
            strike=parsed['strike'],
            expiration=parsed['expiration'],
            bid=bid,
            ask=ask,
            delta=greeks['delta'],
            gamma=greeks['gamma'],
            theta=greeks['theta'],
            vega=greeks['vega'],
            iv=greeks['iv'],
            timestamp=datetime.utcnow()
        )
        
        # Log to Supabase asynchronously
        asyncio.create_task(log_tick_to_supabase(tick))
        
        return tick
        
    except Exception as e:
        logger.error("Failed to fetch option data", symbol=symbol, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stream")
async def start_stream(request: StreamRequest):
    """
    Start streaming real-time option data
    
    Note: This is a simplified implementation. In production, use WebSocket
    with proper connection management.
    """
    # TODO: Implement WebSocket streaming
    # For backtesting and initial implementation, use polling instead
    return {
        "status": "stream_started",
        "symbols": request.symbols,
        "message": "WebSocket streaming not yet implemented. Use /latest endpoint for polling."
    }


@router.get("/latest/{symbol}")
async def get_latest_data(symbol: str) -> LatestDataResponse:
    """
    Get latest option data with Greeks for a specific symbol
    
    Args:
        symbol: Option symbol (e.g., SPY250117C00450000)
    
    Returns:
        Latest OptionTick with calculated Greeks
    """
    try:
        tick = await fetch_option_data_with_greeks(symbol)
        return LatestDataResponse(tick=tick)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error in get_latest_data", symbol=symbol, error=str(e))
        return LatestDataResponse(error=str(e))


@router.get("/health")
async def health_check():
    """Check if data service is operational"""
    return {
        "status": "ok",
        "alpaca_configured": bool(ALPACA_API_KEY and ALPACA_SECRET_KEY),
        "supabase_configured": bool(SUPABASE_URL and SUPABASE_KEY)
    }

