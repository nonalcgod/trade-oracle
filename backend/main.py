"""
Trade Oracle - FastAPI Backend

Main application entry point with all route registrations.
Momentum scalping and IV Mean Reversion strategies live.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import structlog
import os
import asyncio
from contextlib import asynccontextmanager
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ]
)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager.
    Replaces deprecated @app.on_event("startup") and @app.on_event("shutdown")
    """
    # Startup
    logger.info("Trade Oracle starting up",
               environment=os.getenv("ENVIRONMENT", "development"),
               paper_trading=True)

    # Verify environment variables
    required_vars = [
        "ALPACA_API_KEY",
        "ALPACA_SECRET_KEY",
        "SUPABASE_URL",
        "SUPABASE_KEY"
    ]

    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        logger.warning("Missing environment variables", missing=missing_vars)
    else:
        logger.info("All environment variables configured")

    # Start position monitor background task
    from monitoring.position_monitor import monitor_positions
    monitor_task = asyncio.create_task(monitor_positions())
    logger.info("Position monitor started")

    yield  # Application runs here

    # Shutdown
    logger.info("Trade Oracle shutting down")
    monitor_task.cancel()
    try:
        await monitor_task
    except asyncio.CancelledError:
        logger.info("Position monitor stopped gracefully")


# Create FastAPI app with lifespan
app = FastAPI(
    title="Trade Oracle",
    description="IV Mean Reversion options trading system with free-tier services",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configure CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Local development
        "http://localhost:5173",  # Vite default port
        "http://localhost:3004",  # Vite fallback port (when ports in use)
        "https://frontend-nine-mocha-75.vercel.app",  # Production frontend
    ],
    allow_origin_regex=r"http://localhost:\d+|https://.*\.vercel\.app",  # All localhost ports + Vercel
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import routers
from api import data, strategies, risk, execution, testing, iron_condor, momentum_scalping, auto_trade, opening_range_breakout

# Register routers
app.include_router(data.router)
app.include_router(strategies.router)
app.include_router(risk.router)
app.include_router(execution.router)
app.include_router(testing.router)
app.include_router(iron_condor.router)
app.include_router(momentum_scalping.router)
app.include_router(opening_range_breakout.router)
app.include_router(auto_trade.router)


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "Trade Oracle",
        "version": "2.1.0",
        "status": "running",
        "strategies": ["IV Mean Reversion", "0DTE Iron Condor", "0DTE Momentum Scalping", "Opening Range Breakout"],
        "paper_trading": True,
        "endpoints": {
            "docs": "/docs",
            "data": "/api/data",
            "strategies": "/api/strategies",
            "risk": "/api/risk",
            "execution": "/api/execution",
            "iron_condor": "/api/iron-condor",
            "momentum_scalping": "/api/momentum-scalping",
            "orb": "/api/orb",
            "auto_trade": "/api/auto-trade",
            "testing": "/api/testing"
        }
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint for Railway and monitoring
    
    Checks configuration of all services
    """
    alpaca_configured = bool(os.getenv("ALPACA_API_KEY") and os.getenv("ALPACA_SECRET_KEY"))
    supabase_configured = bool(os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_KEY"))
    
    return {
        "status": "healthy",
        "services": {
            "alpaca": "configured" if alpaca_configured else "not_configured",
            "supabase": "configured" if supabase_configured else "not_configured"
        },
        "paper_trading": True
    }




if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", "8000"))
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=os.getenv("ENVIRONMENT") == "development"
    )


# Momentum Scalping deployment marker - force Railway redeploy
