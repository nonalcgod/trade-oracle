"""
Historical Data Fetcher for Backtesting

Fetches options data from Alpaca and caches it locally.
"""

import os
import sys
from pathlib import Path
import json
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict
import pandas as pd
from dotenv import load_dotenv

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

load_dotenv()

# Note: Alpaca's options historical data API has limitations
# For this implementation, we'll create synthetic data based on
# realistic parameters for SPY options

def generate_synthetic_option_data(
    start_date: datetime,
    end_date: datetime,
    underlying_symbol: str = "SPY"
) -> pd.DataFrame:
    """
    Generate synthetic option data for backtesting
    
    This generates realistic option chains with:
    - Multiple strikes around current price
    - Various expirations (30-45 DTE range)
    - Realistic bid/ask spreads
    - IV that varies over time (20-60% range)
    
    In production, replace this with actual Alpaca API calls.
    
    Args:
        start_date: Start of data period
        end_date: End of data period
        underlying_symbol: Stock symbol (default SPY)
    
    Returns:
        DataFrame with columns: date, symbol, underlying_price, strike, 
                               expiration, bid, ask, iv, is_call
    """
    print(f"\nGenerating synthetic option data for {underlying_symbol}...")
    print(f"Period: {start_date.date()} to {end_date.date()}")
    
    data = []
    
    # Simulate daily data
    current_date = start_date
    underlying_price = 450.0  # Starting SPY price
    
    while current_date <= end_date:
        # Simulate price movement (random walk with slight upward drift)
        price_change = (hash(str(current_date)) % 100 - 48) / 10.0  # -4.8 to +5.2
        underlying_price = max(underlying_price + price_change, 100.0)  # Floor at $100
        
        # Generate IV that varies (mean reversion around 25-30%)
        day_hash = hash(str(current_date))
        base_iv = 0.25 + (day_hash % 30) / 100.0  # 0.25 to 0.55
        
        # Create multiple option chains for different expirations
        for dte in [30, 35, 40, 45]:
            expiration = current_date + timedelta(days=dte)
            
            # Create strikes around underlying price
            strikes = [
                underlying_price * 0.95,  # 5% OTM put
                underlying_price * 0.97,  # 3% OTM put
                underlying_price,         # ATM
                underlying_price * 1.03,  # 3% OTM call
                underlying_price * 1.05   # 5% OTM call
            ]
            
            for strike in strikes:
                # Generate both call and put
                for is_call in [True, False]:
                    # Adjust IV based on moneyness (volatility smile)
                    moneyness = strike / underlying_price
                    if is_call:
                        iv_adjustment = abs(moneyness - 1.0) * 0.05  # Slight smile
                    else:
                        iv_adjustment = abs(moneyness - 1.0) * 0.08  # Put skew
                    
                    iv = base_iv + iv_adjustment
                    iv = min(max(iv, 0.15), 0.80)  # Clamp between 15% and 80%
                    
                    # Simple option pricing (not Black-Scholes, just for testing)
                    intrinsic = max(underlying_price - strike, 0) if is_call else max(strike - underlying_price, 0)
                    time_value = iv * strike * (dte / 365.0) ** 0.5 * 0.4
                    theo_price = intrinsic + time_value
                    
                    # Add bid/ask spread (1-2% of price)
                    spread = max(theo_price * 0.015, 0.10)
                    bid = max(theo_price - spread / 2, 0.05)
                    ask = theo_price + spread / 2
                    
                    # Create option symbol (format: SPY250117C00450000)
                    exp_str = expiration.strftime("%y%m%d")
                    option_type = "C" if is_call else "P"
                    strike_str = f"{int(strike * 1000):08d}"
                    symbol = f"{underlying_symbol}{exp_str}{option_type}{strike_str}"
                    
                    data.append({
                        'date': current_date,
                        'symbol': symbol,
                        'underlying_symbol': underlying_symbol,
                        'underlying_price': round(underlying_price, 2),
                        'strike': round(strike, 2),
                        'expiration': expiration,
                        'bid': round(bid, 4),
                        'ask': round(ask, 4),
                        'iv': round(iv, 4),
                        'is_call': is_call,
                        'dte': dte
                    })
        
        # Move to next day (skip weekends)
        current_date += timedelta(days=1)
        if current_date.weekday() >= 5:  # Saturday or Sunday
            current_date += timedelta(days=2 if current_date.weekday() == 5 else 1)
    
    df = pd.DataFrame(data)
    
    print(f"Generated {len(df)} option quotes")
    print(f"Date range: {df['date'].min().date()} to {df['date'].max().date()}")
    print(f"Unique options: {df['symbol'].nunique()}")
    
    return df


def save_to_cache(df: pd.DataFrame, filename: str):
    """Save DataFrame to cache directory"""
    cache_dir = Path(__file__).parent / "cache"
    cache_dir.mkdir(exist_ok=True)
    
    filepath = cache_dir / filename
    df.to_parquet(filepath, index=False)
    print(f"\nSaved data to {filepath}")


def load_from_cache(filename: str) -> pd.DataFrame:
    """Load DataFrame from cache"""
    cache_dir = Path(__file__).parent / "cache"
    filepath = cache_dir / filename
    
    if filepath.exists():
        print(f"Loading cached data from {filepath}")
        return pd.read_parquet(filepath)
    
    return pd.DataFrame()


def fetch_historical_data(
    start_date: datetime,
    end_date: datetime,
    use_cache: bool = True
) -> pd.DataFrame:
    """
    Fetch historical option data (with caching)
    
    Args:
        start_date: Start date
        end_date: End date
        use_cache: Whether to use cached data
    
    Returns:
        DataFrame with historical option data
    """
    cache_filename = f"spy_options_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.parquet"
    
    # Try to load from cache
    if use_cache:
        cached_data = load_from_cache(cache_filename)
        if not cached_data.empty:
            return cached_data
    
    # Generate new data
    print("\nNo cached data found. Generating synthetic data...")
    print("NOTE: In production, this would fetch real data from Alpaca API.")
    
    df = generate_synthetic_option_data(start_date, end_date)
    
    # Save to cache
    save_to_cache(df, cache_filename)
    
    return df


if __name__ == "__main__":
    # Test data fetching
    start = datetime.now() - timedelta(days=730)  # 2 years
    end = datetime.now()
    
    df = fetch_historical_data(start, end, use_cache=False)
    
    print("\n" + "="*60)
    print("DATA SAMPLE")
    print("="*60)
    print(df.head(10))
    print("\n" + "="*60)
    print("DATA SUMMARY")
    print("="*60)
    print(df.describe())

