FROM python:3.9-alpine

# Set working directory
WORKDIR /app

# Copy backend files
COPY backend/ ./backend/

# Install build dependencies for some packages
RUN apk add --no-cache gcc musl-dev libffi-dev

# Install Python dependencies
RUN pip install --no-cache-dir -r backend/requirements-railway.txt

# Expose port (Railway will inject $PORT)
EXPOSE 8000

# Use Hypercorn as recommended by Railway
CMD cd backend && hypercorn main:app --bind [::]:$PORT
