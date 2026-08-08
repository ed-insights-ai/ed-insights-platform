#!/bin/sh
set -e

if [ "${RUN_MIGRATIONS:-false}" = "true" ] || [ "${RUN_MIGRATIONS:-}" = "1" ]; then
  echo "RUN_MIGRATIONS set -- running Alembic migrations..."
  uv run alembic upgrade head
else
  echo "Skipping Alembic migrations (set RUN_MIGRATIONS=true to run them)."
fi

echo "Starting API server..."
exec uv run uvicorn src.main:app --host 0.0.0.0 --port 8000
