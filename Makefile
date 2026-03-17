run:
	uv run python -m uvicorn src.api.app:app --reload --port 8000

migrate:
	uv run python -m alembic upgrade head

migration:
	uv run python -m alembic revision --autogenerate -m "$(msg)"

populate-db:
	docker compose exec -T db psql -U postgres -d misgastos < data/seed-backup.sql

clear-db:
	docker compose exec -T db psql -U postgres -d misgastos -c "TRUNCATE TABLE transactions RESTART IDENTITY CASCADE; TRUNCATE TABLE accounts RESTART IDENTITY CASCADE;"

reset-db:
	docker compose exec -T db psql -U postgres -d misgastos < data/reset.sql

backup-db:
	docker compose exec -T db pg_dump -U postgres --data-only --inserts misgastos > data/backup.sql
