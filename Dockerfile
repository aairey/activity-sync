# Dockerfile for Strava GPX to Nextcloud Sync
FROM python:3.14-alpine

# Set workdir
WORKDIR /app

# Install system dependencies
RUN apk add --no-cache \
    gcc \
    musl-dev \
    libffi-dev

# Install uv
RUN pip install --upgrade pip && \
    pip install uv

# Copy dependency files first for better caching
COPY pyproject.toml uv.lock /app/

# Create virtual environment and install dependencies
RUN uv venv /app/.venv && \
    uv pip install -e /app

# Copy remaining project files
COPY . /app

# Set environment variables (can be overridden at runtime)
ENV PYTHONUNBUFFERED=1
ENV PATH="/app/.venv/bin:$PATH"

# Entrypoint: run the sync daemon
CMD ["python", "-m", "activity_sync.sync_daemon"]
