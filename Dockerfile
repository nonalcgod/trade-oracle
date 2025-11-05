FROM python:3.11.10-slim
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Set working directory to backend (where main.py lives)
WORKDIR /app

# Copy backend files to /app
COPY backend/ ./

# Install Python dependencies
# WORKAROUND: Install supabase LAST to avoid proxy parameter bug (Discussion #35608)
# Upgrade pip first for latest security patches and dependency resolver
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir fastapi==0.115.5 hypercorn==0.17.3 pydantic==2.9.2 \
        pydantic-settings==2.6.1 python-multipart==0.0.18 alpaca-py==0.35.0 \
        upstash-redis==1.0.0 anthropic==0.39.0 python-dotenv==1.0.0 \
        python-dateutil==2.8.2 pytz==2023.3 httpx==0.27.2 websockets==12.0 \
        structlog==24.4.0 && \
    pip install --no-cache-dir supabase==2.15.1

# Run hypercorn on all interfaces using Railway's PORT env var
CMD ["sh", "-c", "hypercorn main:app --bind 0.0.0.0:${PORT:-8000} --keep-alive-timeout 65"]
