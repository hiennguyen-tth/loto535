# ── Build stage ───────────────────────────────────────────────────────────
FROM python:3.12-slim AS base

WORKDIR /app

# Install OS deps (minimal)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps first (layer cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY backend/ ./backend/
COPY frontend/ ./frontend/
COPY init_db.py seed_sample.py import_excel.py startup.py ./

# Create data dir (will be overridden by Fly volume mount)
RUN mkdir -p data

# ── Runtime ───────────────────────────────────────────────────────────────
ENV DB_PATH=/data/lotto535.db
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
# Point Python to find backend package
ENV PYTHONPATH=/app

EXPOSE 8080

# Init DB (auto-seed if empty), then start API
CMD ["sh", "-c", "python startup.py && uvicorn backend.api:app --host 0.0.0.0 --port 8080"]
