"""
Redis Caching Utility for Trade Oracle

Reduces database load by caching frequently accessed data.
Expected impact: 70% reduction in database queries, sub-10ms response times.
"""

import os
import json
import structlog
from typing import Optional, Any
from decimal import Decimal
from datetime import datetime

logger = structlog.get_logger()

# Optional Redis client (graceful fallback if not configured)
redis_client = None

try:
    import redis

    UPSTASH_REDIS_URL = os.getenv("UPSTASH_REDIS_URL")

    if UPSTASH_REDIS_URL:
        redis_client = redis.from_url(
            UPSTASH_REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=2,
            socket_timeout=2
        )
        # Test connection
        redis_client.ping()
        logger.info("Redis cache initialized")
    else:
        logger.warning("UPSTASH_REDIS_URL not configured, caching disabled")

except Exception as e:
    logger.warning("Redis cache initialization failed, running without cache", error=str(e))
    redis_client = None


class JSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for Decimal and datetime types"""

    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


def cache_get(key: str) -> Optional[Any]:
    """
    Get cached value

    Args:
        key: Cache key

    Returns:
        Cached value if exists, None otherwise
    """
    if not redis_client:
        return None

    try:
        data = redis_client.get(key)
        if data:
            logger.debug("Cache hit", key=key)
            return json.loads(data)
        logger.debug("Cache miss", key=key)
        return None
    except Exception as e:
        logger.error("Cache get error", key=key, error=str(e))
        return None


def cache_set(key: str, value: Any, ttl: int = 60) -> bool:
    """
    Set cached value with TTL

    Args:
        key: Cache key
        value: Value to cache (must be JSON serializable)
        ttl: Time to live in seconds

    Returns:
        True if cached successfully, False otherwise
    """
    if not redis_client:
        return False

    try:
        serialized = json.dumps(value, cls=JSONEncoder)
        redis_client.setex(key, ttl, serialized)
        logger.debug("Cache set", key=key, ttl=ttl)
        return True
    except Exception as e:
        logger.error("Cache set error", key=key, error=str(e))
        return False


def cache_delete(key: str) -> bool:
    """
    Delete cached value

    Args:
        key: Cache key

    Returns:
        True if deleted, False otherwise
    """
    if not redis_client:
        return False

    try:
        redis_client.delete(key)
        logger.debug("Cache delete", key=key)
        return True
    except Exception as e:
        logger.error("Cache delete error", key=key, error=str(e))
        return False


def cache_invalidate_pattern(pattern: str) -> int:
    """
    Invalidate all keys matching pattern

    Args:
        pattern: Redis key pattern (e.g., "portfolio:*")

    Returns:
        Number of keys deleted
    """
    if not redis_client:
        return 0

    try:
        keys = redis_client.keys(pattern)
        if keys:
            count = redis_client.delete(*keys)
            logger.info("Cache pattern invalidated", pattern=pattern, count=count)
            return count
        return 0
    except Exception as e:
        logger.error("Cache invalidate error", pattern=pattern, error=str(e))
        return 0


# ============================================================================
# Cache Key Helpers
# ============================================================================

def portfolio_cache_key() -> str:
    """Cache key for portfolio state"""
    return "portfolio:current"


def risk_limits_cache_key() -> str:
    """Cache key for risk limits"""
    return "risk:limits"


def positions_cache_key() -> str:
    """Cache key for open positions list"""
    return "positions:open"


def position_cache_key(position_id: int) -> str:
    """Cache key for individual position"""
    return f"position:{position_id}"


def iv_history_cache_key(symbol: str) -> str:
    """Cache key for 90-day IV history"""
    return f"iv_history:{symbol}"


def trades_cache_key(limit: int) -> str:
    """Cache key for recent trades"""
    return f"trades:recent:{limit}"


# ============================================================================
# Recommended TTL Values (seconds)
# ============================================================================

TTL_RISK_LIMITS = 3600      # 1 hour (rarely change)
TTL_PORTFOLIO = 10          # 10 seconds (frequent updates)
TTL_POSITIONS = 5           # 5 seconds (real-time monitoring)
TTL_IV_HISTORY = 300        # 5 minutes (market data)
TTL_TRADES = 30             # 30 seconds (recent trades)
TTL_OPTION_QUOTE = 0        # Never cache (always fresh)


# ============================================================================
# Cache Statistics
# ============================================================================

def get_cache_stats() -> dict:
    """
    Get Redis cache statistics

    Returns:
        Dict with cache stats (hits, misses, memory usage)
    """
    if not redis_client:
        return {"enabled": False}

    try:
        info = redis_client.info()
        return {
            "enabled": True,
            "connected": True,
            "memory_used": info.get("used_memory_human", "unknown"),
            "total_keys": redis_client.dbsize(),
            "hits": info.get("keyspace_hits", 0),
            "misses": info.get("keyspace_misses", 0),
            "hit_rate": (
                info.get("keyspace_hits", 0) /
                (info.get("keyspace_hits", 0) + info.get("keyspace_misses", 1))
            ) * 100
        }
    except Exception as e:
        logger.error("Cache stats error", error=str(e))
        return {"enabled": True, "connected": False, "error": str(e)}
