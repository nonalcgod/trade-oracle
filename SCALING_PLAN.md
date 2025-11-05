# Trade Oracle Scaling Plan

**Generated:** 2025-11-05
**Based On:** Context7 MCP research of Alpaca Markets, Supabase, Railway, and Vercel

This document outlines the roadmap for scaling Trade Oracle from a functional MVP to a production-grade, high-performance options trading system.

---

## Current Architecture Assessment

### What's Working ✅
- **Backend**: FastAPI on Railway with Uvicorn ASGI server
- **Frontend**: React/Vite on Vercel with TypeScript
- **Database**: Supabase PostgreSQL with proper schema
- **Trading**: Alpaca Paper Trading API integration
- **Deployment**: Automated via GitHub → Railway/Vercel webhooks

### Current Bottlenecks 🔴
1. **REST Polling**: Frontend polls `/api/execution/portfolio` every 5 seconds (inefficient)
2. **Synchronous Data Fetching**: Alpaca REST API calls block request threads
3. **No Caching**: Every request hits database or external APIs
4. **Single Instance**: Railway runs one container (no horizontal scaling)
5. **No Real-Time Updates**: Changes require page refresh or polling cycle
6. **Limited Monitoring**: No performance metrics or alerting

---

## Phase 1: Immediate Optimizations (Week 1-2)

### 1.1 Database Connection Pooling

**Problem**: Each request creates new database connection (slow, resource-intensive)

**Solution**: Implement Supabase connection pooling

```python
# backend/database.py
from supabase import create_client, Client
import os

# Session-based pooling (recommended for serverless)
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

# Connection pooling configuration
supabase: Client = create_client(
    SUPABASE_URL,
    SUPABASE_KEY,
    options={
        "postgrest": {
            "pool": {
                "min_size": 2,
                "max_size": 10,
                "max_idle_time": 300,  # 5 minutes
            }
        }
    }
)
```

**Expected Impact**:
- 30-50% reduction in database query latency
- Better resource utilization under load
- Reduced connection overhead

### 1.2 Response Caching with Redis

**Problem**: Repeatedly fetching unchanged data (risk limits, portfolio state)

**Solution**: Implement Redis caching for read-heavy endpoints

```python
# backend/utils/cache.py
import redis
import os
import json
from datetime import timedelta

redis_client = redis.from_url(
    os.getenv("UPSTASH_REDIS_URL"),
    decode_responses=True
)

def cache_get(key: str):
    """Get cached value"""
    data = redis_client.get(key)
    return json.loads(data) if data else None

def cache_set(key: str, value: dict, ttl: int = 60):
    """Set cached value with TTL in seconds"""
    redis_client.setex(key, ttl, json.dumps(value))

# Usage in routes
@router.get("/api/risk/limits")
async def get_risk_limits():
    cached = cache_get("risk_limits")
    if cached:
        return cached

    limits = {
        "max_portfolio_risk": 0.02,
        "daily_loss_limit": -0.03,
        # ... other limits
    }
    cache_set("risk_limits", limits, ttl=3600)  # Cache for 1 hour
    return limits
```

**Caching Strategy**:
- Risk limits: 1 hour TTL (rarely change)
- Portfolio state: 10 second TTL (frequent updates)
- Historical IV data: 5 minute TTL (market data)
- Option quotes: No caching (always fetch fresh)

**Expected Impact**:
- 70-90% reduction in database queries for cached endpoints
- Sub-10ms response times for cached data
- Reduced load on Supabase free tier

### 1.3 Async Alpaca Client

**Problem**: Synchronous HTTP requests block FastAPI event loop

**Solution**: Use `alpaca-py` async client for concurrent requests

```python
# backend/services/alpaca_service.py
from alpaca.trading.client import TradingClient
from alpaca.data.historical import StockHistoricalDataClient, OptionHistoricalDataClient
from alpaca.data.live import StockDataStream, OptionDataStream
import asyncio

class AlpacaService:
    def __init__(self):
        self.trading_client = TradingClient(
            api_key=os.getenv("ALPACA_API_KEY"),
            secret_key=os.getenv("ALPACA_SECRET_KEY"),
            paper=True  # Paper trading
        )

        self.option_data = OptionHistoricalDataClient(
            api_key=os.getenv("ALPACA_API_KEY"),
            secret_key=os.getenv("ALPACA_SECRET_KEY"),
        )

    async def get_multiple_quotes(self, symbols: list[str]):
        """Fetch quotes for multiple symbols concurrently"""
        async def fetch_quote(symbol):
            return await asyncio.to_thread(
                self.option_data.get_latest_quote, symbol
            )

        tasks = [fetch_quote(symbol) for symbol in symbols]
        return await asyncio.gather(*tasks)
```

**Expected Impact**:
- 5-10x faster when fetching multiple option quotes
- Non-blocking I/O for better concurrency
- Better Railway container utilization

---

## Phase 2: Real-Time Architecture (Week 3-4)

### 2.1 WebSocket Streaming from Alpaca

**Problem**: REST polling wastes API rate limits and adds latency

**Solution**: Implement Alpaca WebSocket streaming for real-time market data

```python
# backend/services/market_stream.py
from alpaca.data.live import OptionDataStream
import asyncio

class MarketStreamService:
    def __init__(self):
        self.stream = OptionDataStream(
            api_key=os.getenv("ALPACA_API_KEY"),
            secret_key=os.getenv("ALPACA_SECRET_KEY"),
        )

        self.watched_symbols = set()

    async def start_streaming(self):
        """Start WebSocket connection to Alpaca"""

        @self.stream.on_quote
        async def on_quote(quote):
            # Process incoming quote
            await self.process_quote(quote)

        # Subscribe to watched symbols
        await self.stream.subscribe_quotes(list(self.watched_symbols))
        await self.stream.run()

    async def process_quote(self, quote):
        """Handle incoming real-time quote"""
        # Calculate Greeks
        # Update Supabase
        # Broadcast to frontend via Supabase real-time
        pass

    def watch_symbol(self, symbol: str):
        """Add symbol to watch list"""
        self.watched_symbols.add(symbol)
```

**Rate Limit Benefits**:
- Current REST polling: 200 requests/minute limit
- WebSocket streaming: Unlimited updates once connected
- No wasted bandwidth on unchanged data

### 2.2 Supabase Real-Time Channels

**Problem**: Frontend polls backend every 5 seconds for updates

**Solution**: Push updates via Supabase real-time subscriptions

```typescript
// frontend/src/hooks/useRealtimePortfolio.ts
import { useEffect, useState } from 'react';
import { createClient } from '@supabase/supabase-js';

const supabase = createClient(
  import.meta.env.VITE_SUPABASE_URL,
  import.meta.env.VITE_SUPABASE_ANON_KEY
);

export function useRealtimePortfolio() {
  const [portfolio, setPortfolio] = useState(null);

  useEffect(() => {
    // Subscribe to portfolio updates
    const channel = supabase
      .channel('portfolio-updates')
      .on(
        'postgres_changes',
        {
          event: 'UPDATE',
          schema: 'public',
          table: 'portfolio_snapshots'
        },
        (payload) => {
          setPortfolio(payload.new);
        }
      )
      .subscribe();

    return () => {
      channel.unsubscribe();
    };
  }, []);

  return portfolio;
}
```

**Backend Trigger** (in Supabase):
```sql
-- Trigger to broadcast portfolio changes
CREATE OR REPLACE FUNCTION notify_portfolio_change()
RETURNS TRIGGER AS $$
BEGIN
  PERFORM pg_notify(
    'portfolio_updates',
    json_build_object('portfolio', NEW)::text
  );
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER portfolio_change_trigger
  AFTER UPDATE ON portfolio_snapshots
  FOR EACH ROW
  EXECUTE FUNCTION notify_portfolio_change();
```

**Expected Impact**:
- Zero polling overhead (push-based updates)
- Sub-second latency for trade notifications
- Better user experience with live updates

### 2.3 Background Tasks with FastAPI

**Problem**: Long-running tasks (backtests, analysis) block HTTP responses

**Solution**: Use FastAPI BackgroundTasks for async processing

```python
# backend/api/execution.py
from fastapi import BackgroundTasks

@router.post("/api/execution/order")
async def execute_order(
    order: OrderRequest,
    background_tasks: BackgroundTasks
):
    # Immediate validation
    risk_check = await risk_service.approve(order)
    if not risk_check.approved:
        raise HTTPException(400, "Risk check failed")

    # Return quickly to user
    order_id = generate_order_id()

    # Execute trade in background
    background_tasks.add_task(
        execute_trade_async,
        order_id,
        order
    )

    return {"order_id": order_id, "status": "pending"}

async def execute_trade_async(order_id: str, order: OrderRequest):
    """Execute trade and update database"""
    # This runs after response is sent
    result = await alpaca_service.place_order(order)
    await database.log_trade(order_id, result)
    # Trigger real-time update to frontend
```

**Expected Impact**:
- API responses < 100ms (don't wait for Alpaca)
- Better error handling (async retries)
- Non-blocking order execution

---

## Phase 3: Horizontal Scaling (Month 2)

### 3.1 Railway Autoscaling Configuration

**Problem**: Single container can't handle traffic spikes

**Solution**: Configure Railway for horizontal scaling

```json
// railway.json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "DOCKERFILE",
    "dockerfilePath": "Dockerfile"
  },
  "deploy": {
    "startCommand": "uvicorn main:app --host 0.0.0.0 --port $PORT --workers 4",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10,
    "healthcheckPath": "/health",
    "healthcheckTimeout": 100,
    "numReplicas": 2,  // Start with 2 instances
    "autoscaling": {
      "enabled": true,
      "minReplicas": 2,
      "maxReplicas": 10,
      "targetCPU": 70,
      "targetMemory": 80
    }
  },
  "regions": ["us-west1"]
}
```

**Dockerfile Optimizations**:
```dockerfile
# Dockerfile (production-optimized)
FROM python:3.11-slim

# Install only runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first (better layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Run with multiple workers
CMD uvicorn main:app \
    --host 0.0.0.0 \
    --port $PORT \
    --workers 4 \
    --log-level info \
    --access-log
```

**Cost Estimate**:
- 2 replicas (baseline): ~$10/month
- Autoscaling to 10 replicas (peak): ~$50/month
- Pay only for what you use (Railway charges per-second)

### 3.2 Vercel Edge Functions

**Problem**: High latency for international users

**Solution**: Deploy critical endpoints as Vercel Edge Functions

```typescript
// frontend/api/health.ts (Edge Function)
export const config = {
  runtime: 'edge',
};

export default async function handler(request: Request) {
  const backendUrl = process.env.VITE_API_URL;

  // Cache health checks
  const cacheKey = `health-${backendUrl}`;
  const cached = await caches.default.match(cacheKey);

  if (cached) {
    return cached;
  }

  const response = await fetch(`${backendUrl}/health`);
  const data = await response.json();

  const newResponse = new Response(JSON.stringify(data), {
    headers: {
      'Content-Type': 'application/json',
      'Cache-Control': 'public, s-maxage=60',
    },
  });

  // Cache for 1 minute
  await caches.default.put(cacheKey, newResponse.clone());

  return newResponse;
}
```

**Expected Impact**:
- Global CDN distribution (sub-50ms latency worldwide)
- Reduced Railway bandwidth costs
- Better frontend performance

### 3.3 Database Indexing Strategy

**Problem**: Slow queries on large `option_ticks` table

**Solution**: Strategic indexing for common query patterns

```sql
-- High-priority indexes for Trade Oracle

-- 1. IV rank calculation (most common query)
CREATE INDEX idx_option_ticks_symbol_timestamp
  ON option_ticks(symbol, timestamp DESC);

-- 2. Historical lookback queries
CREATE INDEX idx_option_ticks_timestamp
  ON option_ticks(timestamp DESC);

-- 3. Trade history queries
CREATE INDEX idx_trades_timestamp
  ON trades(timestamp DESC);

-- 4. Portfolio snapshot queries
CREATE INDEX idx_portfolio_snapshots_timestamp
  ON portfolio_snapshots(timestamp DESC);

-- 5. Strategy-specific: Find elevated IV options
CREATE INDEX idx_option_ticks_iv
  ON option_ticks(iv DESC)
  WHERE timestamp > NOW() - INTERVAL '90 days';

-- Analyze tables after indexing
ANALYZE option_ticks;
ANALYZE trades;
ANALYZE portfolio_snapshots;
```

**Query Optimization Example**:
```python
# Before: Full table scan (slow)
query = supabase.table("option_ticks") \
    .select("*") \
    .eq("symbol", symbol) \
    .order("timestamp", desc=True) \
    .limit(2160)  # 90 days @ 1 tick/hour

# After: Index scan (fast)
# Same query, but index makes it 100x faster
```

**Expected Impact**:
- 90-day IV rank queries: 5000ms → 50ms
- Trade history queries: 1000ms → 10ms
- Support for 100K+ ticks without performance degradation

---

## Phase 4: Performance Monitoring (Month 3)

### 4.1 Logging and Observability

**Railway Logging Configuration**:
```python
# backend/utils/logger.py
import logging
import sys
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    """Structured logging for Railway"""
    def format(self, record):
        log_obj = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
        }

        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_obj)

# Configure logger
logger = logging.getLogger("trade_oracle")
logger.setLevel(logging.INFO)

handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(JSONFormatter())
logger.addHandler(handler)

# Usage
logger.info("Order executed", extra={
    "order_id": "abc123",
    "symbol": "SPY",
    "pnl": 150.25
})
```

### 4.2 Performance Metrics

**Add metrics endpoints**:
```python
# backend/api/metrics.py
from fastapi import APIRouter
from prometheus_client import Counter, Histogram, generate_latest

router = APIRouter()

# Metrics
order_counter = Counter('orders_total', 'Total orders placed')
order_latency = Histogram('order_latency_seconds', 'Order execution time')
api_requests = Counter('api_requests_total', 'Total API requests', ['endpoint', 'status'])

@router.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(
        content=generate_latest(),
        media_type="text/plain"
    )

# Middleware for request tracking
@app.middleware("http")
async def track_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time

    api_requests.labels(
        endpoint=request.url.path,
        status=response.status_code
    ).inc()

    return response
```

**Expected Monitoring**:
- Request latency percentiles (p50, p95, p99)
- Error rates by endpoint
- Order execution success rate
- Database query performance
- External API (Alpaca) response times

### 4.3 Alerting Strategy

**Critical Alerts** (immediate attention):
- Circuit breaker triggered (daily loss limit exceeded)
- Order execution failure rate > 5%
- Database connection pool exhausted
- Railway container crash/restart
- Alpaca API rate limit exceeded

**Warning Alerts** (investigate soon):
- API response time p95 > 500ms
- Database query time > 1 second
- Win rate drops below 50% (strategy degradation)
- Consecutive losses = 2 (approaching circuit breaker)

**Tools**:
- Railway built-in monitoring (free)
- Upstash Redis for rate limiting
- Supabase dashboard for database metrics
- Custom alerting via Discord/Slack webhooks

---

## Cost Analysis and Optimization

### Current Free Tier Limits

| Service | Free Tier | Current Usage | Headroom |
|---------|-----------|---------------|----------|
| Railway | $5 trial credit | ~$2/month (1 container) | 25 days remaining |
| Vercel | Unlimited | <1% of limits | 99%+ available |
| Supabase | 500MB DB, 2GB bandwidth | ~50MB, 200MB/month | 90%+ available |
| Alpaca | Unlimited paper trading | N/A | ∞ |
| Upstash Redis | 10K commands/day | ~2K/day (if implemented) | 80% available |

### Paid Tier Costs (Projected)

**Scenario: 1000 daily API requests, 100 trades/month**

- Railway: $10/month (2 replicas with autoscaling)
- Vercel: $0/month (stays on free tier)
- Supabase: $0/month (stays on free tier, <500MB)
- Upstash: $0/month (stays on free tier)
- **Total: $10/month**

**Scenario: 10K daily requests, 500 trades/month**

- Railway: $25/month (4-6 replicas average)
- Vercel: $0/month (still free)
- Supabase: $25/month (Pro tier for connection pooling)
- Upstash: $10/month (pay-as-you-go)
- **Total: $60/month**

### Cost Optimization Strategies

1. **Lazy Replicas**: Scale to 0 during non-trading hours (9pm-9am PT)
2. **Efficient Queries**: Use database indexes to reduce Supabase bandwidth
3. **CDN Caching**: Serve static assets from Vercel edge (unlimited)
4. **Batch Operations**: Group database writes to reduce transactions
5. **Rate Limiting**: Prevent runaway API calls with Redis throttling

---

## Implementation Priority

### High Priority (Do First) 🔴
1. Database connection pooling → Immediate 30% performance gain
2. Response caching with Redis → Reduce database load
3. Database indexing → Enable fast IV rank queries
4. Async Alpaca client → Better concurrency

### Medium Priority (Do Next) 🟡
5. WebSocket streaming from Alpaca → Real-time market data
6. Supabase real-time channels → Push updates to frontend
7. Background tasks → Non-blocking order execution
8. Railway autoscaling → Handle traffic spikes

### Low Priority (Do Later) 🟢
9. Vercel Edge Functions → Optimize for global users
10. Performance monitoring → Prometheus metrics
11. Advanced alerting → Discord/Slack notifications
12. Load testing → Validate scaling assumptions

---

## Risk Mitigation

### Technical Risks

**Risk**: WebSocket connection drops during market hours
**Mitigation**: Auto-reconnect logic with exponential backoff, fallback to REST polling

**Risk**: Railway autoscaling too aggressive (high costs)
**Mitigation**: Set maxReplicas=10, monitor costs daily, implement circuit breakers

**Risk**: Supabase connection pool exhausted
**Mitigation**: Implement connection retry logic, monitor pool utilization, upgrade to Pro tier if needed

**Risk**: Alpaca rate limits exceeded
**Mitigation**: WebSocket streaming (no rate limits), request throttling, exponential backoff

### Financial Risks

**Risk**: Unexpected Railway costs from autoscaling
**Mitigation**: Set monthly budget alert at $20, maxReplicas cap, review usage weekly

**Risk**: Supabase bandwidth overages
**Mitigation**: Implement caching, optimize queries, monitor bandwidth daily

---

## Success Metrics

### Performance Targets

- API response time (p95): < 200ms
- Database query time (p95): < 50ms
- Order execution time: < 2 seconds
- Real-time update latency: < 500ms
- Uptime: > 99.9% (excluding planned maintenance)

### Scalability Targets

- Support 10K API requests/day without degradation
- Handle 500 concurrent WebSocket connections
- Process 100 trades/day with <1% error rate
- Store 1M+ option ticks without query slowdown

### Business Metrics

- Win rate: > 60% (backtested: 75%)
- Sharpe ratio: > 1.5 (backtested: 1.8)
- Maximum drawdown: < 15%
- Average trade duration: 7-14 days

---

## Next Steps

1. **Immediate**: Implement Phase 1 optimizations (connection pooling, caching, async client)
2. **Week 2**: Add database indexes and validate query performance
3. **Week 3**: Implement WebSocket streaming and real-time architecture
4. **Week 4**: Configure Railway autoscaling and test under load
5. **Month 2**: Deploy monitoring and alerting infrastructure
6. **Month 3**: Load testing and optimization based on real usage patterns

---

## References

- Alpaca Markets API Docs: https://docs.alpaca.markets
- Supabase Performance Guide: https://supabase.com/docs/guides/database/performance
- Railway Scaling Guide: https://docs.railway.app/reference/scaling
- Vercel Edge Functions: https://vercel.com/docs/functions/edge-functions
- FastAPI Background Tasks: https://fastapi.tiangolo.com/tutorial/background-tasks/

---

**Document Status**: Draft v1.0
**Last Updated**: 2025-11-05
**Approval Status**: Pending user review
