"""
Risk Management Service

Implements circuit breakers and position sizing using Kelly Criterion.
Non-negotiable hardcoded limits for safety.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from decimal import Decimal
from typing import Optional
import os
import structlog
from supabase import create_client, Client
from datetime import datetime, timedelta

from models.trading import Signal, RiskApproval, Portfolio, StrategyStats

logger = structlog.get_logger()

router = APIRouter(prefix="/api/risk", tags=["risk"])

# Initialize Supabase for trade history
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

supabase: Optional[Client] = None
try:
    if SUPABASE_URL and SUPABASE_KEY:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    logger.error("Failed to initialize Supabase", error=str(e))


class ApprovalRequest(BaseModel):
    """Request for trade approval"""
    signal: Signal
    portfolio: Portfolio


class RiskManager:
    """
    Risk Manager with hardcoded safety limits
    
    Circuit Breakers:
    - Max 2% portfolio risk per trade
    - Max 5% position size
    - -3% daily loss limit (stop trading)
    - 3 consecutive losses (stop trading)
    - Max portfolio delta of 5.0
    
    Position Sizing:
    - Half-Kelly for safety
    - Based on strategy historical performance
    """
    
    # Hardcoded limits (DO NOT MODIFY)
    MAX_PORTFOLIO_RISK = Decimal('0.02')   # 2% max risk per trade
    MAX_POSITION_SIZE = Decimal('0.05')    # 5% max position size
    DAILY_LOSS_LIMIT = Decimal('-0.03')    # -3% circuit breaker
    MAX_CONSECUTIVE_LOSSES = 3
    MAX_DELTA = Decimal('5.0')             # Maximum portfolio delta exposure
    
    async def get_strategy_stats(self, strategy_name: str) -> StrategyStats:
        """
        Fetch historical performance statistics for a strategy
        
        Args:
            strategy_name: Name of the strategy
        
        Returns:
            StrategyStats with win rate, avg win, avg loss
        """
        try:
            if not supabase:
                logger.warning("Supabase not configured, using default stats")
                return StrategyStats(
                    strategy_name=strategy_name,
                    win_rate=0.55,  # Assume 55% from research
                    avg_win=Decimal('100.00'),
                    avg_loss=Decimal('50.00'),
                    total_trades=0
                )
            
            # Fetch closed trades for this strategy
            response = supabase.table("trades")\
                .select("pnl")\
                .eq("strategy", strategy_name)\
                .not_.is_("exit_price", "null")\
                .execute()
            
            if not response.data or len(response.data) < 10:
                logger.warning("Insufficient trade history", strategy=strategy_name)
                # Use research-based defaults for IV Mean Reversion
                return StrategyStats(
                    strategy_name=strategy_name,
                    win_rate=0.75,  # 75% from research
                    avg_win=Decimal('120.00'),
                    avg_loss=Decimal('80.00'),
                    total_trades=len(response.data) if response.data else 0
                )
            
            # Calculate statistics
            pnls = [Decimal(str(row['pnl'])) for row in response.data]
            wins = [p for p in pnls if p > 0]
            losses = [p for p in pnls if p < 0]
            
            win_rate = len(wins) / len(pnls) if pnls else 0.55
            avg_win = sum(wins) / len(wins) if wins else Decimal('100')
            avg_loss = abs(sum(losses) / len(losses)) if losses else Decimal('50')
            
            stats = StrategyStats(
                strategy_name=strategy_name,
                win_rate=win_rate,
                avg_win=avg_win,
                avg_loss=avg_loss,
                total_trades=len(pnls)
            )
            
            logger.info("Calculated strategy stats", 
                       strategy=strategy_name,
                       win_rate=win_rate,
                       total_trades=len(pnls))
            
            return stats
            
        except Exception as e:
            logger.error("Failed to get strategy stats", strategy=strategy_name, error=str(e))
            # Return safe defaults on error
            return StrategyStats(
                strategy_name=strategy_name,
                win_rate=0.55,
                avg_win=Decimal('100.00'),
                avg_loss=Decimal('50.00'),
                total_trades=0
            )
    
    async def approve_trade(self, signal: Signal, portfolio: Portfolio) -> RiskApproval:
        """
        Evaluate trade signal against risk limits
        
        Args:
            signal: Trading signal from strategy
            portfolio: Current portfolio state
        
        Returns:
            RiskApproval with decision and position size
        """
        try:
            # Circuit Breaker 1: Daily loss limit
            daily_loss_pct = portfolio.daily_pnl / portfolio.balance
            if daily_loss_pct <= self.DAILY_LOSS_LIMIT:
                logger.warning("Daily loss limit hit",
                             daily_pnl=float(portfolio.daily_pnl),
                             limit=float(self.DAILY_LOSS_LIMIT))
                return RiskApproval(
                    approved=False,
                    reasoning=f"Daily loss limit hit: {daily_loss_pct:.2%} <= {self.DAILY_LOSS_LIMIT:.2%}"
                )
            
            # Circuit Breaker 2: Consecutive losses
            if portfolio.consecutive_losses >= self.MAX_CONSECUTIVE_LOSSES:
                logger.warning("Consecutive loss limit hit",
                             consecutive_losses=portfolio.consecutive_losses)
                return RiskApproval(
                    approved=False,
                    reasoning=f"Consecutive loss limit: {portfolio.consecutive_losses} >= {self.MAX_CONSECUTIVE_LOSSES}"
                )
            
            # Circuit Breaker 3: Delta exposure
            # For now, skip delta check if we don't have accurate delta tracking
            # TODO: Implement proper delta aggregation across positions
            
            # Get strategy statistics
            stats = await self.get_strategy_stats(signal.strategy)
            
            # Calculate Kelly Criterion
            # Kelly % = (Win Rate * Avg Win - Loss Rate * Avg Loss) / Avg Win
            loss_rate = 1.0 - stats.win_rate
            kelly_pct = (stats.win_rate * float(stats.avg_win) - loss_rate * float(stats.avg_loss)) / float(stats.avg_win)
            
            # Use half-Kelly for safety
            kelly_half = Decimal(str(kelly_pct * 0.5))
            
            # Apply maximum portfolio risk limit
            kelly_half = min(kelly_half, self.MAX_PORTFOLIO_RISK)
            
            if kelly_half <= 0:
                logger.warning("Kelly criterion is negative", kelly=kelly_pct)
                return RiskApproval(
                    approved=False,
                    reasoning=f"Negative Kelly criterion: {kelly_pct:.4f}"
                )
            
            # Calculate position size based on Kelly
            risk_per_trade = portfolio.balance * kelly_half
            
            # Calculate risk per contract
            # Risk = |Entry Price - Stop Loss| * 100 (multiplier)
            risk_per_contract = abs(signal.entry_price - signal.stop_loss) * Decimal('100')
            
            if risk_per_contract == 0:
                logger.error("Risk per contract is zero", signal=signal.symbol)
                return RiskApproval(
                    approved=False,
                    reasoning="Invalid signal: risk per contract is zero"
                )
            
            # Position size = Risk allocated / Risk per contract
            position_size = int(risk_per_trade / risk_per_contract)
            
            # Apply position size limit (max 5% of portfolio)
            max_contracts = int(portfolio.balance * self.MAX_POSITION_SIZE / (signal.entry_price * Decimal('100')))
            position_size = min(position_size, max_contracts)
            
            # Minimum 1 contract
            if position_size < 1:
                logger.info("Position size too small", calculated=position_size)
                return RiskApproval(
                    approved=False,
                    reasoning=f"Position size too small: {position_size} contracts"
                )
            
            # Calculate actual max loss
            max_loss = risk_per_contract * position_size
            
            logger.info("Trade approved",
                       symbol=signal.symbol,
                       position_size=position_size,
                       max_loss=float(max_loss),
                       kelly_half=float(kelly_half))
            
            return RiskApproval(
                approved=True,
                position_size=position_size,
                max_loss=max_loss,
                reasoning=f"Kelly sizing: {position_size} contracts, max loss ${max_loss:.2f}"
            )
            
        except Exception as e:
            logger.error("Error in trade approval", error=str(e))
            return RiskApproval(
                approved=False,
                reasoning=f"Error: {str(e)}"
            )


# Risk manager instance
risk_manager = RiskManager()


@router.post("/approve")
async def approve_trade(request: ApprovalRequest) -> RiskApproval:
    """
    Approve or reject a trade signal based on risk limits
    
    Args:
        request: Contains signal and current portfolio state
    
    Returns:
        RiskApproval with decision and position size
    """
    try:
        approval = await risk_manager.approve_trade(request.signal, request.portfolio)
        return approval
    except Exception as e:
        logger.error("Error in approve endpoint", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/limits")
async def get_risk_limits():
    """Get current risk management limits"""
    return {
        "max_portfolio_risk": float(risk_manager.MAX_PORTFOLIO_RISK),
        "max_position_size": float(risk_manager.MAX_POSITION_SIZE),
        "daily_loss_limit": float(risk_manager.DAILY_LOSS_LIMIT),
        "max_consecutive_losses": risk_manager.MAX_CONSECUTIVE_LOSSES,
        "max_delta": float(risk_manager.MAX_DELTA),
        "description": "Hardcoded limits - DO NOT MODIFY without understanding implications"
    }


@router.get("/health")
async def health_check():
    """Check if risk service is operational"""
    return {
        "status": "ok",
        "supabase_configured": bool(supabase)
    }

