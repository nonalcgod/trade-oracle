FROM python:3.11.10-slim
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Set working directory to backend (where main.py lives)
WORKDIR /app

# Copy backend files to /app
COPY backend/ ./

# Install Python dependencies
# FIX: Remove explicit httpx pin - let supabase pull its own compatible version
# Switch to Uvicorn (more reliable than Hypercorn for Railway)
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir fastapi==0.115.5 uvicorn[standard]==0.32.1 pydantic==2.9.2 \
        pydantic-settings==2.6.1 python-multipart==0.0.18 alpaca-py==0.35.0 \
        upstash-redis==1.0.0 anthropic==0.39.0 python-dotenv==1.0.0 \
        python-dateutil==2.8.2 pytz==2023.3 websockets==12.0 \
        structlog==24.4.0 supabase==2.15.1

# Run uvicorn on all interfaces using Railway's PORT env var
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
