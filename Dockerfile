FROM python:3.11
ENV PYTHONUNBUFFERED=1

# Force Railway cache bust - deployment d5fffde
# Set working directory to backend (where main.py lives)
WORKDIR /app

# Copy backend files to /app
COPY backend/ ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements-railway.txt

# Run hypercorn on all interfaces using Railway's PORT env var
CMD ["sh", "-c", "hypercorn main:app --bind 0.0.0.0:${PORT:-8000} --keep-alive-timeout 65"]
