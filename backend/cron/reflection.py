"""
Weekly Reflection - Claude AI Analysis

Runs weekly (Sunday 6 PM) to analyze trading performance and generate insights.
This is a Phase 4 feature but creating the skeleton now.
"""

import os
from datetime import datetime, timezone, timedelta
from decimal import Decimal
import asyncio
import structlog
from anthropic import Anthropic
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

logger = structlog.get_logger()

# Initialize clients
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")


async def fetch_weekly_trades():
    """Fetch trades from the past week"""
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Get trades from last 7 days
        cutoff = datetime.now(timezone.utc) - timedelta(days=7)
        
        response = supabase.table("trades")\
            .select("*")\
            .gte("timestamp", cutoff.isoformat())\
            .execute()
        
        return response.data if response.data else []
    
    except Exception as e:
        logger.error("Failed to fetch weekly trades", error=str(e))
        return []


async def analyze_with_claude(trades):
    """
    Use Claude to analyze trading performance
    
    Args:
        trades: List of trades from the past week
    
    Returns:
        Analysis text from Claude
    """
    try:
        if not ANTHROPIC_API_KEY:
            logger.warning("Anthropic API key not configured")
            return "Claude analysis not available (API key not configured)"
        
        client = Anthropic(api_key=ANTHROPIC_API_KEY)
        
        # Prepare trade data for Claude
        trade_summary = {
            "total_trades": len(trades),
            "wins": sum(1 for t in trades if t.get('pnl', 0) > 0),
            "losses": sum(1 for t in trades if t.get('pnl', 0) < 0),
            "total_pnl": sum(Decimal(str(t.get('pnl', 0))) for t in trades),
            "avg_pnl": sum(Decimal(str(t.get('pnl', 0))) for t in trades) / len(trades) if trades else 0
        }
        
        # Create prompt
        prompt = f"""Analyze this week's options trading performance:

Total Trades: {trade_summary['total_trades']}
Wins: {trade_summary['wins']}
Losses: {trade_summary['losses']}
Win Rate: {trade_summary['wins'] / trade_summary['total_trades'] * 100:.1f}% if trades else 0
Total P&L: ${trade_summary['total_pnl']:.2f}
Average P&L per Trade: ${trade_summary['avg_pnl']:.2f}

Strategy: IV Mean Reversion (buy underpriced, sell overpriced options)

Please provide:
1. Performance assessment
2. Any concerning patterns
3. Recommendations for next week
4. Risk management observations

Keep analysis concise and actionable."""

        # Call Claude
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        analysis = message.content[0].text
        
        logger.info("Claude analysis complete", trade_count=len(trades))
        
        return analysis
    
    except Exception as e:
        logger.error("Failed to analyze with Claude", error=str(e))
        return f"Analysis failed: {str(e)}"


async def save_reflection(analysis, metrics):
    """Save reflection to Supabase"""
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        data = {
            "week_ending": datetime.now(timezone.utc).date().isoformat(),
            "analysis": {"text": analysis},
            "metrics": metrics
        }
        
        supabase.table("reflections").insert(data).execute()
        
        logger.info("Reflection saved to Supabase")
    
    except Exception as e:
        logger.error("Failed to save reflection", error=str(e))


async def run_weekly_reflection():
    """Main function to run weekly reflection"""
    logger.info("Starting weekly reflection")
    
    try:
        # Fetch trades
        trades = await fetch_weekly_trades()
        
        if not trades:
            logger.info("No trades this week, skipping reflection")
            return
        
        # Calculate metrics
        metrics = {
            "total_trades": len(trades),
            "wins": sum(1 for t in trades if t.get('pnl', 0) > 0),
            "losses": sum(1 for t in trades if t.get('pnl', 0) < 0),
            "total_pnl": float(sum(Decimal(str(t.get('pnl', 0))) for t in trades)),
            "win_rate": sum(1 for t in trades if t.get('pnl', 0) > 0) / len(trades) if trades else 0
        }
        
        # Analyze with Claude
        analysis = await analyze_with_claude(trades)
        
        # Save reflection
        await save_reflection(analysis, metrics)
        
        logger.info("Weekly reflection complete", metrics=metrics)
        
        print(f"\n{'='*60}")
        print("WEEKLY REFLECTION")
        print(f"{'='*60}")
        print(f"\nMetrics:")
        print(f"  Total Trades: {metrics['total_trades']}")
        print(f"  Win Rate: {metrics['win_rate']*100:.1f}%")
        print(f"  Total P&L: ${metrics['total_pnl']:.2f}")
        print(f"\nClaude Analysis:")
        print(analysis)
        print(f"\n{'='*60}\n")
    
    except Exception as e:
        logger.error("Weekly reflection failed", error=str(e))


if __name__ == "__main__":
    # Run reflection
    asyncio.run(run_weekly_reflection())

