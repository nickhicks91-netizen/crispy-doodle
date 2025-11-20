# EchoZero v4.2.1 - Production Dockerfile
# Multi-stage build for optimized image size

# Stage 1: Base image with Python and CUDA support
FROM nvidia/cuda:12.1.0-cudnn8-runtime-ubuntu22.04 AS base

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install Python 3.11 and system dependencies
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3.11-dev \
    python3-pip \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create symlinks for python
RUN ln -sf /usr/bin/python3.11 /usr/bin/python && \
    ln -sf /usr/bin/python3.11 /usr/bin/python3

# Upgrade pip
RUN python -m pip install --upgrade pip setuptools wheel

# Stage 2: Dependencies
FROM base AS dependencies

WORKDIR /tmp

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Stage 3: Application
FROM base AS application

# Set working directory
WORKDIR /app

# Copy installed packages from dependencies stage
COPY --from=dependencies /usr/local/lib/python3.11/dist-packages /usr/local/lib/python3.11/dist-packages

# Copy application code
COPY config/ /app/config/
COPY src/ /app/src/
COPY tests/ /app/tests/

# Create necessary directories
RUN mkdir -p /app/logs /app/checkpoints /app/data

# Set environment variables
ENV PYTHONPATH=/app \
    ECHOZERO_CONFIG_PATH=/app/config/dimensions.yaml \
    ECHOZERO_CHECKPOINT_DIR=/app/checkpoints \
    ECHOZERO_LOG_DIR=/app/logs

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose API port
EXPOSE 8000

# Non-root user for security
RUN useradd -m -u 1000 echozero && \
    chown -R echozero:echozero /app
USER echozero

# Default command: run API server
CMD ["python", "-m", "uvicorn", "src.api.server:app", "--host", "0.0.0.0", "--port", "8000"]
