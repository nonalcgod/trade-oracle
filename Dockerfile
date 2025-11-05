FROM python:3.11.10-slim
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Set working directory to backend (where main.py lives)
WORKDIR /app

# Copy backend files to /app
COPY backend/ ./

# Install Python dependencies
# Upgrade pip first for latest security patches and dependency resolver
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements-railway.txt

# Run hypercorn on all interfaces using Railway's PORT env var
CMD ["sh", "-c", "hypercorn main:app --bind 0.0.0.0:${PORT:-8000} --keep-alive-timeout 65"]
