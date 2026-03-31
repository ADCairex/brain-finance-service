#!/bin/sh
set -e

echo "Running migrations..."
CURRENT=$(uv run alembic current 2>/dev/null || echo "none")
if echo "$CURRENT" | grep -q "head"; then
  echo "Alembic up to date, running upgrade..."
  uv run alembic upgrade head
elif echo "$CURRENT" | grep -q "none"; then
  # No alembic_version yet — check if tables already exist (legacy DB)
  HAS_TABLES=$(uv run python -c "
from src.api.config import settings
from sqlalchemy import create_engine, inspect
engine = create_engine(settings.database_url)
tables = inspect(engine).get_table_names()
print('yes' if 'accounts' in tables else 'no')
  ")
  if [ "$HAS_TABLES" = "yes" ]; then
    echo "Legacy DB detected, stamping current state..."
    uv run alembic stamp head
  else
    echo "Fresh DB, running migrations from scratch..."
    uv run alembic upgrade head
  fi
else
  uv run alembic upgrade head
fi

echo "Starting server..."
exec uv run python -m uvicorn src.api.app:app --host 0.0.0.0 --port 8002 ${UVICORN_ARGS:-}
