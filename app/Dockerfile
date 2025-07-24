# Production Dockerfile for Flask app
FROM python:3.11-slim

# Set working directory to root to match module structure
WORKDIR /

# Set environment variables
ENV PYTHONPATH=/
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies including netcat-openbsd
RUN apt-get update && apt-get install -y \
    default-mysql-client \
    netcat-openbsd \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip and install setuptools first
RUN pip install --upgrade pip setuptools wheel

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy wait-for-db script and set execute permission
COPY wait-for-db.sh .
RUN chmod +x wait-for-db.sh

# Copy application code
COPY . .