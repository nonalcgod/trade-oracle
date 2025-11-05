FROM python:3.9-slim

# Set working directory to backend (where main.py lives)
WORKDIR /app

# Copy backend files to /app
COPY backend/ ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements-railway.txt

# Run hypercorn on all interfaces using Railway's PORT env var
# Using :: for IPv6/IPv4 dual stack binding (Railway recommendation)
CMD ["sh", "-c", "hypercorn main:app --bind [::]:${PORT:-8000}"]
