FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
    PORT=8000

WORKDIR /app

# System deps: build tools for native wheels, curl for healthcheck,
# libpq5 for psycopg[asyncio] (pure-Python psycopg v3 needs the libpq shared lib)
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl \
        build-essential \
        libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps first so the layer is cached across code changes
COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers + their OS-level dependencies
RUN playwright install --with-deps chromium

# Copy application code
COPY . .

# Create non-root user and hand over ownership
RUN useradd --create-home --shell /bin/bash neuroagent \
    && chown -R neuroagent:neuroagent /app /ms-playwright
USER neuroagent

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl --fail http://localhost:${PORT}/api/v1/health || exit 1

# Run DB migrations then start the server.
# Railway injects $PORT — fall back to 8000 for local Docker runs.
CMD sh -c "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"
