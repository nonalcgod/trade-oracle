FROM python:3.9-slim
ENV PYTHONUNBUFFERED=1

# Set working directory to backend (where main.py lives)
WORKDIR /app

# Copy backend files to /app
COPY backend/ ./

# Install Python dependencies and validate installation
RUN pip install --no-cache-dir -r requirements-railway.txt && \
    python -c "import fastapi; import hypercorn; import alpaca; import supabase; print('✓ Dependencies installed successfully')"

# Run hypercorn on all interfaces using Railway's PORT env var
CMD ["sh", "-c", "hypercorn main:app --bind 0.0.0.0:${PORT:-8000} --keep-alive-timeout 65"]
