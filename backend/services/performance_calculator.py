"""
Performance Calculator Service

Calculates strategy performance metrics for copy trading evaluation.
Determines if strategies are ready for live capital based on statistical criteria.
"""

from decimal import Decimal
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import math
from supabase import Client
import structlog

logger = structlog.get_logger()


class PerformanceMetrics:
    """Container for calculated performance metrics"""

    def __init__(self):
        self.total_trades: int = 0
        self.wins: int = 0
        self.losses: int = 0
        self.win_rate: Decimal = Decimal("0")
        self.total_pnl: Decimal = Decimal("0")
        self.average_win: Decimal = Decimal("0")
        self.average_loss: Decimal = Decimal("0")
        self.largest_win: Decimal = Decimal("0")
        self.largest_loss: Decimal = Decimal("0")
        self.profit_factor: Decimal = Decimal("0")
        self.sharpe_ratio: Decimal = Decimal("0")
        self.max_drawdown: Decimal = Decimal("0")
        self.confidence_score: Decimal = Decimal("0")
        self.ready_for_live: bool = False
        self.ready_reason: str = ""


def calculate_win_rate(trades: List[Dict]) -> Decimal:
    """Calculate percentage of winning trades"""
    if not trades:
        return Decimal("0")

    wins = sum(1 for t in trades if Decimal(str(t.get('pnl', 0))) > 0)
    return Decimal(str(wins / len(trades) * 100)).quantize(Decimal("0.01"))


def calculate_profit_factor(trades: List[Dict]) -> Decimal:
    """
    Calculate profit factor (gross profit / gross loss)

    > 2.0 is excellent
    1.5-2.0 is good
    < 1.0 is losing system
    """
    if not trades:
        return Decimal("0")

    gross_profit = sum(
        Decimal(str(t.get('pnl', 0)))
        for t in trades
        if Decimal(str(t.get('pnl', 0))) > 0
    )

    gross_loss = abs(sum(
        Decimal(str(t.get('pnl', 0)))
        for t in trades
        if Decimal(str(t.get('pnl', 0))) < 0
    ))

    if gross_loss == 0:
        return Decimal("999")  # All winners (cap at 999)

    profit_factor = (gross_profit / gross_loss).quantize(Decimal("0.01"))
    return min(profit_factor, Decimal("999"))


def calculate_sharpe_ratio(trades: List[Dict], risk_free_rate: Decimal = Decimal("0.04")) -> Decimal:
    """
    Calculate Sharpe ratio (risk-adjusted return)

    > 2.0 is excellent
    1.5-2.0 is very good
    1.0-1.5 is good
    < 1.0 is suboptimal
    """
    if len(trades) < 2:
        return Decimal("0")

    # Calculate returns
    returns = [Decimal(str(t.get('pnl', 0))) for t in trades]

    # Mean return
    mean_return = sum(returns) / len(returns)

    # Standard deviation
    variance = sum((r - mean_return) ** 2 for r in returns) / (len(returns) - 1)
    std_dev = Decimal(str(math.sqrt(float(variance))))

    if std_dev == 0:
        return Decimal("0")

    # Annualized Sharpe (assuming ~252 trading days)
    excess_return = mean_return - (risk_free_rate / Decimal("252"))
    sharpe = (excess_return / std_dev) * Decimal(str(math.sqrt(252)))

    return sharpe.quantize(Decimal("0.01"))


def calculate_max_drawdown(trades: List[Dict]) -> Decimal:
    """
    Calculate maximum peak-to-trough decline

    < 5% is excellent
    5-10% is acceptable
    10-20% is concerning
    > 20% is dangerous
    """
    if not trades:
        return Decimal("0")

    # Sort by timestamp
    sorted_trades = sorted(trades, key=lambda t: t.get('timestamp', ''))

    # Calculate cumulative P&L
    cumulative_pnl = Decimal("0")
    peak = Decimal("0")
    max_dd = Decimal("0")

    for trade in sorted_trades:
        pnl = Decimal(str(trade.get('pnl', 0)))
        cumulative_pnl += pnl

        # Update peak
        if cumulative_pnl > peak:
            peak = cumulative_pnl

        # Calculate drawdown from peak
        drawdown = ((peak - cumulative_pnl) / peak * 100) if peak > 0 else Decimal("0")

        # Update max drawdown
        if drawdown > max_dd:
            max_dd = drawdown

    return max_dd.quantize(Decimal("0.01"))


def calculate_confidence_score(
    total_trades: int,
    win_rate: Decimal,
    sharpe_ratio: Decimal,
    max_drawdown: Decimal
) -> Decimal:
    """
    Calculate confidence score (0-100) for strategy readiness

    Based on:
    - Sample size (more trades = higher confidence)
    - Win rate consistency (higher = higher confidence)
    - Risk-adjusted returns (higher Sharpe = higher confidence)
    - Risk management (lower drawdown = higher confidence)

    90-100: PROVEN - Ready for live capital
    75-89:  PROMISING - Need more validation
    60-74:  UNCERTAIN - Needs significant work
    0-59:   NOT READY - Don't trade live
    """
    score = Decimal("0")

    # Sample size component (max 40 points)
    if total_trades >= 150:
        score += Decimal("40")
    elif total_trades >= 100:
        score += Decimal("35")
    elif total_trades >= 50:
        score += Decimal("25")
    elif total_trades >= 30:
        score += Decimal("15")
    else:
        score += Decimal("10")

    # Win rate component (max 30 points)
    if win_rate >= 75:
        score += Decimal("30")
    elif win_rate >= 70:
        score += Decimal("25")
    elif win_rate >= 65:
        score += Decimal("20")
    elif win_rate >= 60:
        score += Decimal("15")
    elif win_rate >= 55:
        score += Decimal("10")
    else:
        score += Decimal("5")

    # Sharpe ratio component (max 20 points)
    if sharpe_ratio >= 2.0:
        score += Decimal("20")
    elif sharpe_ratio >= 1.5:
        score += Decimal("15")
    elif sharpe_ratio >= 1.0:
        score += Decimal("10")
    else:
        score += Decimal("5")

    # Drawdown component (max 10 points)
    if max_drawdown <= 5:
        score += Decimal("10")
    elif max_drawdown <= 10:
        score += Decimal("7")
    elif max_drawdown <= 15:
        score += Decimal("5")
    else:
        score += Decimal("2")

    return min(score, Decimal("100"))


async def calculate_strategy_performance(
    supabase: Client,
    strategy_name: str,
    month: str,
    trading_mode: str = "paper"
) -> PerformanceMetrics:
    """
    Calculate comprehensive performance metrics for a strategy

    Args:
        supabase: Supabase client
        strategy_name: Strategy identifier (IV_MEAN_REVERSION, IRON_CONDOR, MOMENTUM_SCALPING)
        month: Month to analyze (format: 'YYYY-MM')
        trading_mode: 'paper' or 'live'

    Returns:
        PerformanceMetrics object with all calculated metrics
    """
    metrics = PerformanceMetrics()

    try:
        # Fetch trades for strategy
        response = supabase.table('trades').select('*').filter(
            'strategy_name', 'eq', strategy_name
        ).filter(
            'trading_mode', 'eq', trading_mode
        ).execute()

        trades = response.data if response.data else []

        # Filter by month
        month_trades = [
            t for t in trades
            if t.get('timestamp', '').startswith(month)
        ]

        if not month_trades:
            logger.info("No trades found", strategy=strategy_name, month=month)
            return metrics

        # Calculate basic metrics
        metrics.total_trades = len(month_trades)
        metrics.wins = sum(1 for t in month_trades if Decimal(str(t.get('pnl', 0))) > 0)
        metrics.losses = metrics.total_trades - metrics.wins
        metrics.win_rate = calculate_win_rate(month_trades)

        # Calculate P&L metrics
        metrics.total_pnl = sum(Decimal(str(t.get('pnl', 0))) for t in month_trades)

        winning_trades = [t for t in month_trades if Decimal(str(t.get('pnl', 0))) > 0]
        losing_trades = [t for t in month_trades if Decimal(str(t.get('pnl', 0))) <= 0]

        if winning_trades:
            metrics.average_win = sum(Decimal(str(t.get('pnl', 0))) for t in winning_trades) / len(winning_trades)
            metrics.largest_win = max(Decimal(str(t.get('pnl', 0))) for t in winning_trades)

        if losing_trades:
            metrics.average_loss = sum(Decimal(str(t.get('pnl', 0))) for t in losing_trades) / len(losing_trades)
            metrics.largest_loss = min(Decimal(str(t.get('pnl', 0))) for t in losing_trades)

        # Calculate advanced metrics
        metrics.profit_factor = calculate_profit_factor(month_trades)
        metrics.sharpe_ratio = calculate_sharpe_ratio(month_trades)
        metrics.max_drawdown = calculate_max_drawdown(month_trades)

        # Calculate confidence score
        metrics.confidence_score = calculate_confidence_score(
            metrics.total_trades,
            metrics.win_rate,
            metrics.sharpe_ratio,
            metrics.max_drawdown
        )

        # Determine readiness for live trading
        # Fetch criteria from database
        criteria_response = supabase.table('strategy_criteria').select('*').filter(
            'strategy_name', 'eq', strategy_name
        ).execute()

        if criteria_response.data and len(criteria_response.data) > 0:
            criteria = criteria_response.data[0]

            min_trades = criteria.get('min_trades_required', 100)
            min_win_rate = Decimal(str(criteria.get('min_win_rate', 65)))
            min_sharpe = Decimal(str(criteria.get('min_sharpe_ratio', 1.5)))
            max_dd = Decimal(str(criteria.get('max_drawdown_threshold', 10)))

            # Check all criteria
            reasons = []

            if metrics.total_trades < min_trades:
                reasons.append(f"Need {min_trades - metrics.total_trades} more trades")

            if metrics.win_rate < min_win_rate:
                reasons.append(f"Win rate {metrics.win_rate}% below required {min_win_rate}%")

            if metrics.sharpe_ratio < min_sharpe:
                reasons.append(f"Sharpe {metrics.sharpe_ratio} below required {min_sharpe}")

            if metrics.max_drawdown > max_dd:
                reasons.append(f"Drawdown {metrics.max_drawdown}% exceeds max {max_dd}%")

            if not reasons:
                metrics.ready_for_live = True
                metrics.ready_reason = "✅ All criteria met - Ready for live capital"
            else:
                metrics.ready_for_live = False
                metrics.ready_reason = "; ".join(reasons)

        logger.info(
            "Performance calculated",
            strategy=strategy_name,
            month=month,
            trades=metrics.total_trades,
            win_rate=float(metrics.win_rate),
            sharpe=float(metrics.sharpe_ratio),
            confidence=float(metrics.confidence_score),
            ready=metrics.ready_for_live
        )

        return metrics

    except Exception as e:
        logger.error("Failed to calculate performance", error=str(e), strategy=strategy_name)
        return metrics


async def update_monthly_performance(
    supabase: Client,
    strategy_name: str,
    month: Optional[str] = None,
    trading_mode: str = "paper"
) -> None:
    """
    Update strategy_performance table with latest metrics

    This is called automatically after each trade via database trigger,
    but can also be called manually to recalculate.
    """
    if month is None:
        month = datetime.now().strftime("%Y-%m")

    # Calculate metrics
    metrics = await calculate_strategy_performance(supabase, strategy_name, month, trading_mode)

    if metrics.total_trades == 0:
        logger.info("No trades to update", strategy=strategy_name, month=month)
        return

    # Upsert to strategy_performance table
    try:
        data = {
            'strategy_name': strategy_name,
            'month': month,
            'trading_mode': trading_mode,
            'total_trades': metrics.total_trades,
            'wins': metrics.wins,
            'losses': metrics.losses,
            'win_rate': float(metrics.win_rate),
            'total_pnl': float(metrics.total_pnl),
            'average_win': float(metrics.average_win),
            'average_loss': float(metrics.average_loss),
            'largest_win': float(metrics.largest_win),
            'largest_loss': float(metrics.largest_loss),
            'sharpe_ratio': float(metrics.sharpe_ratio),
            'profit_factor': float(metrics.profit_factor),
            'max_drawdown': float(metrics.max_drawdown),
            'confidence_score': float(metrics.confidence_score),
            'sample_size_adequate': metrics.total_trades >= 100,
            'ready_for_live': metrics.ready_for_live,
            'ready_for_live_reason': metrics.ready_reason,
            'updated_at': datetime.now().isoformat()
        }

        # Check if record exists
        existing = supabase.table('strategy_performance').select('id').filter(
            'strategy_name', 'eq', strategy_name
        ).filter(
            'month', 'eq', month
        ).filter(
            'trading_mode', 'eq', trading_mode
        ).execute()

        if existing.data and len(existing.data) > 0:
            # Update existing record
            supabase.table('strategy_performance').update(data).filter(
                'strategy_name', 'eq', strategy_name
            ).filter(
                'month', 'eq', month
            ).filter(
                'trading_mode', 'eq', trading_mode
            ).execute()
        else:
            # Insert new record
            supabase.table('strategy_performance').insert(data).execute()

        logger.info(
            "Performance updated in database",
            strategy=strategy_name,
            month=month,
            confidence=float(metrics.confidence_score)
        )

    except Exception as e:
        logger.error("Failed to update performance table", error=str(e), strategy=strategy_name)
