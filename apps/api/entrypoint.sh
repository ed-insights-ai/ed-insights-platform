#!/bin/sh
set -e

echo "Running Alembic migrations..."
uv run alembic upgrade head

echo "Starting API server..."
exec uv run uvicorn src.main:app --host 0.0.0.0 --port 8000
