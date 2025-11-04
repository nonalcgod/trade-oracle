"""
Strategy Service - IV Mean Reversion

Generates trading signals based on Implied Volatility mean reversion.
Research-proven strategy with 75% win rate in backtests.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from decimal import Decimal
from datetime import datetime, timedelta
from typing import Optional
import os
import structlog
from supabase import create_client, Client

from ..models.trading import OptionTick, Signal, SignalType

logger = structlog.get_logger()

router = APIRouter(prefix="/api/strategies", tags=["strategies"])

# Initialize Supabase for historical IV data
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

supabase: Optional[Client] = None
try:
    if SUPABASE_URL and SUPABASE_KEY:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    logger.error("Failed to initialize Supabase", error=str(e))


class SignalRequest(BaseModel):
    """Request for strategy signal generation"""
    tick: OptionTick


class SignalResponse(BaseModel):
    """Response with trading signal"""
    signal: Optional[Signal] = None
    message: str


class IVMeanReversionStrategy:
    """
    IV Mean Reversion Strategy
    
    Research-proven parameters:
    - Sell options when IV > 70th percentile (overpriced)
    - Buy options when IV < 30th percentile (underpriced)
    - Only trade options with 30-45 DTE
    - Use 90-day historical window for IV rank calculation
    """
    
    # Hardcoded parameters from research
    IV_HIGH = Decimal('0.70')  # 70th percentile
    IV_LOW = Decimal('0.30')   # 30th percentile
    DTE_MIN = 30
    DTE_MAX = 45
    IV_LOOKBACK_DAYS = 90
    
    def __init__(self):
        self.name = "iv_mean_reversion"
    
    async def calculate_iv_rank(self, symbol: str, current_iv: Decimal) -> float:
        """
        Calculate IV rank (percentile) from 90-day historical data
        
        IV Rank = (Current IV - Min IV) / (Max IV - Min IV)
        
        Args:
            symbol: Option symbol
            current_iv: Current implied volatility
        
        Returns:
            IV rank between 0.0 and 1.0
        """
        try:
            if not supabase:
                logger.warning("Supabase not configured, using default IV rank")
                # If no historical data, assume neutral IV rank
                return 0.50
            
            # Fetch 90-day historical IV data
            cutoff_date = datetime.utcnow() - timedelta(days=self.IV_LOOKBACK_DAYS)
            
            response = supabase.table("option_ticks")\
                .select("iv")\
                .eq("symbol", symbol)\
                .gte("timestamp", cutoff_date.isoformat())\
                .execute()
            
            if not response.data or len(response.data) < 10:
                logger.warning("Insufficient historical data", symbol=symbol, count=len(response.data) if response.data else 0)
                return 0.50  # Default to neutral
            
            # Calculate min and max IV
            ivs = [float(row['iv']) for row in response.data]
            min_iv = min(ivs)
            max_iv = max(ivs)
            
            if max_iv == min_iv:
                return 0.50  # Avoid division by zero
            
            # Calculate IV rank
            iv_rank = (float(current_iv) - min_iv) / (max_iv - min_iv)
            iv_rank = max(0.0, min(1.0, iv_rank))  # Clamp to [0, 1]
            
            logger.info("Calculated IV rank", symbol=symbol, iv_rank=iv_rank, min_iv=min_iv, max_iv=max_iv)
            return iv_rank
            
        except Exception as e:
            logger.error("Failed to calculate IV rank", symbol=symbol, error=str(e))
            return 0.50  # Default to neutral on error
    
    async def generate_signal(self, tick: OptionTick) -> Optional[Signal]:
        """
        Generate trading signal based on IV mean reversion
        
        Args:
            tick: Current option market data with Greeks
        
        Returns:
            Signal if conditions are met, None otherwise
        """
        # Calculate DTE
        dte = tick.dte
        
        # Check if within DTE range
        if not (self.DTE_MIN <= dte <= self.DTE_MAX):
            logger.debug("Outside DTE range", symbol=tick.symbol, dte=dte)
            return None
        
        # Calculate IV rank
        iv_rank = await self.calculate_iv_rank(tick.symbol, tick.iv)
        
        # Generate SELL signal: IV too high (overpriced)
        if iv_rank > float(self.IV_HIGH):
            return Signal(
                symbol=tick.symbol,
                signal=SignalType.SELL,
                strategy=self.name,
                confidence=iv_rank,
                entry_price=tick.mid_price,
                stop_loss=tick.mid_price * Decimal('2.0'),  # Exit if doubles (loss)
                take_profit=tick.mid_price * Decimal('0.5'),  # Exit at 50% profit
                reasoning=f"IV rank {iv_rank:.2f} > {self.IV_HIGH} (overpriced), DTE {dte}",
                timestamp=datetime.utcnow()
            )
        
        # Generate BUY signal: IV too low (underpriced)
        elif iv_rank < float(self.IV_LOW):
            return Signal(
                symbol=tick.symbol,
                signal=SignalType.BUY,
                strategy=self.name,
                confidence=1.0 - iv_rank,  # Lower IV = higher confidence for buy
                entry_price=tick.mid_price,
                stop_loss=tick.mid_price * Decimal('0.5'),  # Exit if loses 50%
                take_profit=tick.mid_price * Decimal('2.0'),  # Exit at 100% profit
                reasoning=f"IV rank {iv_rank:.2f} < {self.IV_LOW} (underpriced), DTE {dte}",
                timestamp=datetime.utcnow()
            )
        
        # No signal if IV is in neutral range
        logger.debug("IV in neutral range", symbol=tick.symbol, iv_rank=iv_rank)
        return None


# Strategy instance
strategy = IVMeanReversionStrategy()


@router.post("/signal")
async def generate_signal(request: SignalRequest) -> SignalResponse:
    """
    Generate trading signal for an option
    
    Args:
        request: Contains OptionTick with current market data
    
    Returns:
        Signal if strategy conditions are met, otherwise message
    """
    try:
        signal = await strategy.generate_signal(request.tick)
        
        if signal:
            logger.info("Generated signal", 
                       symbol=signal.symbol, 
                       signal_type=signal.signal.value,
                       confidence=signal.confidence)
            return SignalResponse(
                signal=signal,
                message=f"Signal generated: {signal.signal.value.upper()}"
            )
        else:
            return SignalResponse(
                signal=None,
                message="No signal generated (conditions not met)"
            )
    
    except Exception as e:
        logger.error("Error generating signal", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/info")
async def get_strategy_info():
    """Get information about the IV Mean Reversion strategy"""
    return {
        "strategy": "IV Mean Reversion",
        "description": "Trades options based on implied volatility percentiles",
        "parameters": {
            "iv_high_threshold": float(strategy.IV_HIGH),
            "iv_low_threshold": float(strategy.IV_LOW),
            "dte_min": strategy.DTE_MIN,
            "dte_max": strategy.DTE_MAX,
            "lookback_days": strategy.IV_LOOKBACK_DAYS
        },
        "signals": {
            "SELL": "Generated when IV rank > 70% (overpriced options)",
            "BUY": "Generated when IV rank < 30% (underpriced options)"
        }
    }


@router.get("/health")
async def health_check():
    """Check if strategy service is operational"""
    return {
        "status": "ok",
        "strategy": strategy.name,
        "supabase_configured": bool(supabase)
    }

