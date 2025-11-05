"""
IV Data Seeding Script

Seeds historical IV data for testing signal generation.
Creates realistic 90-day IV history for option symbols.
"""

import asyncio
import os
import sys
from decimal import Decimal
from datetime import datetime, timedelta
import random

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from dotenv import load_dotenv
load_dotenv()

import structlog
from supabase import create_client

logger = structlog.get_logger()

# Initialize Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def generate_iv_series(
    days: int = 90,
    base_iv: float = 0.30,
    volatility: float = 0.05,
    trending: str = "mean_reverting"
) -> list[float]:
    """
    Generate realistic IV series

    Args:
        days: Number of days to generate
        base_iv: Base IV level (default 30%)
        volatility: IV volatility (how much it swings)
        trending: "mean_reverting", "trending_up", or "trending_down"

    Returns:
        List of IV values
    """
    ivs = []
    current_iv = base_iv

    for i in range(days):
        # Mean reversion factor
        mean_reversion = (base_iv - current_iv) * 0.1

        # Random walk
        shock = random.gauss(0, volatility)

        # Trend component
        if trending == "trending_up":
            trend = 0.001
        elif trending == "trending_down":
            trend = -0.001
        else:
            trend = 0

        # Update IV
        current_iv += mean_reversion + shock + trend
        current_iv = max(0.10, min(2.0, current_iv))  # Clamp between 10% and 200%

        ivs.append(current_iv)

    return ivs


async def seed_option_data(
    symbol: str,
    underlying_price: float,
    strike: float,
    base_iv: float = 0.30,
    trending: str = "mean_reverting",
    days: int = 90
):
    """
    Seed historical IV data for an option

    Args:
        symbol: Option symbol (OCC format)
        underlying_price: Current underlying price
        strike: Option strike price
        base_iv: Base IV level
        trending: IV trend pattern
        days: Number of days of history
    """
    try:
        logger.info("Seeding IV data",
                   symbol=symbol,
                   underlying_price=underlying_price,
                   strike=strike,
                   days=days)

        # Generate IV series
        iv_series = generate_iv_series(days, base_iv, 0.05, trending)

        # Generate price series (correlated with IV)
        price_series = []
        current_price = underlying_price
        for iv in iv_series:
            # Price changes correlated with IV
            price_change_pct = random.gauss(0, iv * 0.3)  # Higher IV = bigger moves
            current_price *= (1 + price_change_pct)
            price_series.append(current_price)

        # Reverse so newest is last
        iv_series.reverse()
        price_series.reverse()

        # Insert data points
        now = datetime.utcnow()
        inserted = 0

        for i, (iv, underlying_px) in enumerate(zip(iv_series, price_series)):
            # One data point per day
            timestamp = now - timedelta(days=days-i)

            # Calculate option price (simplified Black-Scholes approximation)
            # ATM option is roughly underlying_price * IV * sqrt(DTE/365)
            dte = max(45 - (days - i) // 2, 1)  # Decreasing DTE
            option_price = underlying_px * iv * (dte / 365) ** 0.5

            # Bid/ask spread
            spread = option_price * 0.02  # 2% spread
            bid = option_price - spread / 2
            ask = option_price + spread / 2

            data = {
                "timestamp": timestamp.isoformat(),
                "symbol": symbol,
                "underlying_price": round(underlying_px, 2),
                "strike": strike,
                "bid": round(bid, 4),
                "ask": round(ask, 4),
                "delta": None,  # Would need full BS calculation
                "gamma": None,
                "theta": None,
                "vega": None,
                "iv": round(iv, 6)
            }

            try:
                supabase.table("option_ticks").insert(data).execute()
                inserted += 1
            except Exception as e:
                logger.error("Failed to insert tick", timestamp=timestamp, error=str(e))

        logger.info("Seeding complete",
                   symbol=symbol,
                   inserted=inserted,
                   last_iv=f"{iv_series[-1]:.2%}")

        # Calculate and log IV rank
        current_iv = iv_series[-1]
        below_current = sum(1 for iv in iv_series if iv < current_iv)
        iv_rank = below_current / len(iv_series)

        logger.info("IV Rank calculated",
                   symbol=symbol,
                   current_iv=f"{current_iv:.2%}",
                   iv_rank=f"{iv_rank:.1%}",
                   signal="BUY" if iv_rank < 0.30 else "SELL" if iv_rank > 0.70 else "NEUTRAL")

        return {
            "symbol": symbol,
            "inserted": inserted,
            "current_iv": current_iv,
            "iv_rank": iv_rank
        }

    except Exception as e:
        logger.error("Seeding failed", symbol=symbol, error=str(e))
        return None


async def seed_test_scenarios():
    """
    Seed multiple scenarios for testing

    Creates options with different IV patterns to test signal generation
    """
    scenarios = [
        {
            "name": "Low IV (BUY Signal)",
            "symbol": "SPY251219C00600000",
            "underlying_price": 600.0,
            "strike": 600.0,
            "base_iv": 0.20,
            "trending": "trending_down"
        },
        {
            "name": "High IV (SELL Signal)",
            "symbol": "QQQ251219C00640000",
            "underlying_price": 640.0,
            "strike": 640.0,
            "base_iv": 0.50,
            "trending": "trending_up"
        },
        {
            "name": "Mean Reverting (NEUTRAL)",
            "symbol": "IWM251219C00230000",
            "underlying_price": 230.0,
            "strike": 230.0,
            "base_iv": 0.30,
            "trending": "mean_reverting"
        }
    ]

    results = []

    for scenario in scenarios:
        print(f"\n{'='*80}")
        print(f"Seeding: {scenario['name']}")
        print(f"{'='*80}")

        result = await seed_option_data(
            symbol=scenario['symbol'],
            underlying_price=scenario['underlying_price'],
            strike=scenario['strike'],
            base_iv=scenario['base_iv'],
            trending=scenario['trending']
        )

        results.append({
            "name": scenario['name'],
            "result": result
        })

        # Small delay between scenarios
        await asyncio.sleep(0.5)

    return results


async def main():
    """Main seeding function"""
    print("\n" + "="*80)
    print("TRADE ORACLE - IV DATA SEEDING")
    print("="*80)
    print(f"Database: {SUPABASE_URL}")
    print(f"Time: {datetime.now().isoformat()}")
    print("="*80)

    # Seed test scenarios
    results = await seed_test_scenarios()

    # Summary
    print("\n" + "="*80)
    print("SEEDING SUMMARY")
    print("="*80)

    for item in results:
        name = item['name']
        result = item['result']

        if result:
            print(f"\n✅ {name}")
            print(f"   Symbol: {result['symbol']}")
            print(f"   Inserted: {result['inserted']} data points")
            print(f"   Current IV: {result['current_iv']:.2%}")
            print(f"   IV Rank: {result['iv_rank']:.1%}")

            if result['iv_rank'] < 0.30:
                print(f"   Signal: 🟢 BUY (IV < 30th percentile)")
            elif result['iv_rank'] > 0.70:
                print(f"   Signal: 🔴 SELL (IV > 70th percentile)")
            else:
                print(f"   Signal: ⚪ NEUTRAL")
        else:
            print(f"\n❌ {name} - Seeding failed")

    print("\n" + "="*80)
    print("✅ SEEDING COMPLETE")
    print("="*80)
    print("\nNext steps:")
    print("1. Check dashboard: https://trade-oracle-lac.vercel.app")
    print("2. Test signal generation via API")
    print("3. Execute test trades with /api/testing/simulate-signal")
    print()


if __name__ == "__main__":
    asyncio.run(main())
