#!/bin/sh
set -e

if [ "${RUN_MIGRATIONS:-true}" = "true" ] || [ "${RUN_MIGRATIONS:-}" = "1" ]; then
  echo "Running Alembic migrations..."
  uv run alembic upgrade head
else
  echo "Skipping Alembic migrations (RUN_MIGRATIONS=${RUN_MIGRATIONS})."
fi

echo "Starting API server..."
exec uv run uvicorn src.main:app --host 0.0.0.0 --port 8000
