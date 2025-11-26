# Container image for running the Fashion Concierge API server.
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Pre-copy dependency metadata for better Docker layer caching
COPY pyproject.toml README.md /app/
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir .

# Copy application source
COPY . /app

# Application configuration is injected via environment variables or
# Secret Manager mounted environment variables (see deploy/cloudrun-service.yaml).
ENV APP_ENV=production

EXPOSE 8080
CMD ["uvicorn", "server.api:app", "--host", "0.0.0.0", "--port", "8080"]
