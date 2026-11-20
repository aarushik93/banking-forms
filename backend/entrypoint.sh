#!/bin/sh
set -e

echo "Running database migrations..."
alembic upgrade head

# PORT is injected by managed hosts (Render); defaults to 8000 for compose/local.
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}" --workers "${WEB_CONCURRENCY:-2}"
