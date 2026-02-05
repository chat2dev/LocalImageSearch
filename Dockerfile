# Dockerfile for Image Auto-Tagging System
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install uv package manager via pip (no apt-get needed)
RUN pip install --no-cache-dir uv

# Copy project files
COPY pyproject.toml uv.lock* ./
COPY requirements.txt ./
COPY prompts.yaml ./
COPY src/ ./src/
COPY scripts/ ./scripts/

# Create data directory
RUN mkdir -p ./data

# Install dependencies using uv
RUN uv sync

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Default command
CMD ["bash"]
