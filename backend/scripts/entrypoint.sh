#!/bin/sh
set -e

echo "⏳ Waiting for PostgreSQL to become available..."
until python -c "import psycopg2; psycopg2.connect('${DATABASE_SYNC_URL}')" 2>/dev/null; do
  echo "PostgreSQL is unavailable - sleeping 1s"
  sleep 1
done

echo "✅ PostgreSQL is up and running!"

echo "🔄 Running Alembic migrations..."
alembic upgrade head

echo "🌱 Running database seed (idempotent)..."
python scripts/seed.py || true

echo "🚀 Starting FastAPI server on port 8000..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
