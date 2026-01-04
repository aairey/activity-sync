# Dockerfile for Strava GPX to Nextcloud Sync
FROM python:3.14-alpine

# Set workdir
WORKDIR /app

# Install system dependencies
RUN apk add --no-cache \
    gcc \
    musl-dev \
    libffi-dev

# Copy project files
COPY . /app

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install uv && \
    uv pip install --system --requirement <(uv pip compile pyproject.toml)

# Set environment variables (can be overridden at runtime)
ENV PYTHONUNBUFFERED=1

# Entrypoint: run the sync daemon
CMD ["uv", "run", "python", "-m", "activity_sync.sync_daemon"]
