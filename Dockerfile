# SmartOrder PRO - Production Dockerfile
# by MAIGA ABOUBACAR
# 
# Build: docker build -t smartorder-pro .
# Run: docker run -d --name smartorder smartorder-pro

FROM python:3.11-slim

LABEL maintainer="MAIGA ABOUBACAR"
LABEL description="SmartOrder PRO - AI Trading System"
LABEL version="v2.0"

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    libssl-dev \
    libffi-dev \
    python3-dev \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for better caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p logs security monitoring exchange_connectors

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV MODE=live
ENV LOG_LEVEL=INFO

# Expose ports
EXPOSE 5000 8555

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5000/api/status || exit 1

# Create non-root user for security
RUN useradd -m -u 1000 smartorder && \
    chown -R smartorder:smartorder /app

USER smartorder

# Default command
CMD ["python", "web_dashboard.py"]
