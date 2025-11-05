FROM python:3.9-alpine

# Set working directory
WORKDIR /app

# Copy backend files
COPY backend/ ./backend/

# Install build dependencies for some packages
RUN apk add --no-cache gcc musl-dev libffi-dev

# Install Python dependencies
RUN pip install --no-cache-dir -r backend/requirements-railway.txt

# Change to backend directory
WORKDIR /app/backend

# Use Hypercorn as recommended by Railway (dual-stack binding)
CMD hypercorn main:app --bind [::]:${PORT:-8000}
