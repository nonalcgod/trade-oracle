"""
Async Alpaca Client Wrapper

Provides async methods for Alpaca API calls with concurrent execution support.
Expected 5-10x performance improvement when fetching multiple quotes.
"""

import asyncio
import os
from decimal import Decimal
from datetime import datetime
from typing import List, Optional
import structlog

from alpaca.trading.client import TradingClient
from alpaca.data.historical import OptionHistoricalDataClient
from alpaca.data.requests import OptionLatestQuoteRequest
from alpaca.trading.requests import LimitOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce

logger = structlog.get_logger()


class AsyncAlpacaClient:
    """
    Async wrapper for Alpaca API calls

    Converts synchronous Alpaca SDK calls to async using asyncio.to_thread
    for non-blocking I/O and concurrent request support.
    """

    def __init__(self):
        """Initialize Alpaca clients"""
        self.api_key = os.getenv("ALPACA_API_KEY")
        self.secret_key = os.getenv("ALPACA_SECRET_KEY")

        if not self.api_key or not self.secret_key:
            logger.warning("Alpaca credentials not configured")
            self.trading_client = None
            self.data_client = None
            return

        # Initialize clients (paper trading)
        self.trading_client = TradingClient(
            self.api_key,
            self.secret_key,
            paper=True
        )

        self.data_client = OptionHistoricalDataClient(
            self.api_key,
            self.secret_key
        )

        logger.info("Async Alpaca client initialized (PAPER TRADING)")

    async def get_account(self):
        """
        Get account information asynchronously

        Returns:
            Account object with balance, positions, etc.
        """
        if not self.trading_client:
            return None

        try:
            account = await asyncio.to_thread(
                self.trading_client.get_account
            )
            return account
        except Exception as e:
            logger.error("Failed to get account", error=str(e))
            return None

    async def get_positions(self):
        """
        Get all open positions asynchronously

        Returns:
            List of Position objects from Alpaca
        """
        if not self.trading_client:
            return []

        try:
            positions = await asyncio.to_thread(
                self.trading_client.get_all_positions
            )
            return positions
        except Exception as e:
            logger.error("Failed to get positions", error=str(e))
            return []

    async def get_option_quote(self, symbol: str):
        """
        Get latest option quote asynchronously

        Args:
            symbol: Option symbol (OCC format)

        Returns:
            OptionQuote object
        """
        if not self.data_client:
            return None

        try:
            request = OptionLatestQuoteRequest(symbol_or_symbols=[symbol])
            quotes = await asyncio.to_thread(
                self.data_client.get_option_latest_quote,
                request
            )
            return quotes.get(symbol) if quotes else None
        except Exception as e:
            logger.error("Failed to get option quote", symbol=symbol, error=str(e))
            return None

    async def get_multiple_quotes(self, symbols: List[str]):
        """
        Get quotes for multiple symbols concurrently

        This is the key performance improvement - fetches all quotes in parallel.

        Args:
            symbols: List of option symbols

        Returns:
            Dict of {symbol: quote}
        """
        if not symbols:
            return {}

        try:
            # Create tasks for concurrent execution
            tasks = [self.get_option_quote(symbol) for symbol in symbols]

            # Execute all requests concurrently
            quotes = await asyncio.gather(*tasks)

            # Map results back to symbols
            return {symbol: quote for symbol, quote in zip(symbols, quotes) if quote}

        except Exception as e:
            logger.error("Failed to get multiple quotes", error=str(e))
            return {}

    async def place_order(
        self,
        symbol: str,
        quantity: int,
        side: OrderSide,
        limit_price: Decimal
    ):
        """
        Place limit order asynchronously

        Args:
            symbol: Option symbol
            quantity: Number of contracts
            side: BUY or SELL
            limit_price: Limit price per contract

        Returns:
            Order object from Alpaca
        """
        if not self.trading_client:
            return None

        try:
            request = LimitOrderRequest(
                symbol=symbol,
                qty=quantity,
                side=side,
                time_in_force=TimeInForce.DAY,
                limit_price=float(limit_price)
            )

            order = await asyncio.to_thread(
                self.trading_client.submit_order,
                request
            )

            logger.info("Order placed",
                       symbol=symbol,
                       quantity=quantity,
                       side=side.value,
                       limit_price=float(limit_price),
                       order_id=order.id)

            return order

        except Exception as e:
            logger.error("Failed to place order",
                        symbol=symbol,
                        error=str(e))
            return None

    async def get_order(self, order_id: str):
        """
        Get order status asynchronously

        Args:
            order_id: Alpaca order ID

        Returns:
            Order object with current status
        """
        if not self.trading_client:
            return None

        try:
            order = await asyncio.to_thread(
                self.trading_client.get_order_by_id,
                order_id
            )
            return order
        except Exception as e:
            logger.error("Failed to get order", order_id=order_id, error=str(e))
            return None

    async def cancel_order(self, order_id: str):
        """
        Cancel order asynchronously

        Args:
            order_id: Alpaca order ID

        Returns:
            True if cancelled successfully
        """
        if not self.trading_client:
            return False

        try:
            await asyncio.to_thread(
                self.trading_client.cancel_order_by_id,
                order_id
            )
            logger.info("Order cancelled", order_id=order_id)
            return True
        except Exception as e:
            logger.error("Failed to cancel order", order_id=order_id, error=str(e))
            return False

    async def get_portfolio_history(self, period: str = "1M"):
        """
        Get portfolio history asynchronously

        Args:
            period: Time period (1D, 1W, 1M, 3M, etc.)

        Returns:
            PortfolioHistory object
        """
        if not self.trading_client:
            return None

        try:
            history = await asyncio.to_thread(
                self.trading_client.get_portfolio_history,
                period=period
            )
            return history
        except Exception as e:
            logger.error("Failed to get portfolio history", error=str(e))
            return None


# Global async client instance
async_alpaca_client = AsyncAlpacaClient()


# ============================================================================
# Helper Functions
# ============================================================================

async def get_portfolio_balance() -> Optional[Decimal]:
    """Get current portfolio balance"""
    account = await async_alpaca_client.get_account()
    if account:
        return Decimal(str(account.equity))
    return None


async def get_open_alpaca_positions():
    """Get all open positions from Alpaca"""
    return await async_alpaca_client.get_positions()


async def fetch_latest_quotes(symbols: List[str]) -> dict:
    """
    Fetch latest quotes for multiple symbols concurrently

    This is the key performance improvement - uses asyncio.gather
    to fetch all quotes in parallel instead of sequentially.

    Args:
        symbols: List of option symbols

    Returns:
        Dict of {symbol: quote}
    """
    return await async_alpaca_client.get_multiple_quotes(symbols)


# ============================================================================
# Performance Comparison
# ============================================================================

async def benchmark_concurrent_quotes(symbols: List[str]):
    """
    Benchmark synchronous vs async quote fetching

    Example usage:
        symbols = ["SPY251219C00600000", "QQQ251219C00640000", "IWM251219C00230000"]
        await benchmark_concurrent_quotes(symbols)
    """
    import time

    # Sequential (old way)
    start = time.time()
    sequential_results = {}
    for symbol in symbols:
        quote = await async_alpaca_client.get_option_quote(symbol)
        sequential_results[symbol] = quote
    sequential_time = time.time() - start

    # Concurrent (new way)
    start = time.time()
    concurrent_results = await fetch_latest_quotes(symbols)
    concurrent_time = time.time() - start

    speedup = sequential_time / concurrent_time if concurrent_time > 0 else 0

    logger.info("Concurrent quote benchmark",
               symbols=len(symbols),
               sequential_time=f"{sequential_time:.3f}s",
               concurrent_time=f"{concurrent_time:.3f}s",
               speedup=f"{speedup:.2f}x")

    return {
        "sequential_time": sequential_time,
        "concurrent_time": concurrent_time,
        "speedup": speedup
    }
