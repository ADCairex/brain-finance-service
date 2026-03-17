# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project context

**brain-finance-service** is the backend microservice for the **MisGastos** personal finance platform. It runs alongside **brain-frontend** (React, `../brain-frontend`) and exposes a REST API at `http://localhost:8000`.

## Commands

```bash
uv sync                                                        # Install dependencies
uv run python -m uvicorn src.api.app:app --reload --port 8000            # Start dev server
uv run python -m uvicorn src.api.app:app --host 0.0.0.0 --port 8000      # Production start

make run                                                       # Alias for dev server
make migrate                                                   # Apply pending Alembic migrations
make migration msg="describe change"                           # Generate new migration
make populate-db                                               # Load seed data
make reset-db                                                  # Reset DB to seed state
make backup-db                                                 # Dump data to data/backup.sql

docker compose up                                              # Start PostgreSQL + pgAdmin
```

Environment: copy `.env.example` to `.env` and set `DATABASE_URL`.

## Architecture

FastAPI + SQLAlchemy (sync) + PostgreSQL. Migrations via Alembic.

```
src/api/
├── app.py               # FastAPI instance, CORS middleware, router registration, create_all
├── config.py            # pydantic-settings: DATABASE_URL from .env
├── database.py          # SQLAlchemy engine, SessionLocal, Base, get_db dependency
├── models.py            # ORM: Account, Transaction, Asset, InvestmentInstrument, Investment
├── schemas.py           # Pydantic I/O schemas + Summary/CategoryBreakdown/MonthlyData
└── endpoints/
    ├── transactions.py  # /api/transactions — CRUD + summary/by-category/by-month
    ├── accounts.py      # /api/accounts — CRUD
    ├── assets.py        # /api/assets — CRUD
    └── investments.py   # /api/investments — CRUD + live prices via yfinance
```

```
data/                    # SQL scripts (seed, reset, backup, migrations)
docs/                    # api-contract.md, db-schema.svg
alembic/                 # Migration env and versions
docker-compose.yml       # PostgreSQL 17 + pgAdmin 4
```

## Key patterns

- **DB session**: injected via `Depends(get_db)` in every endpoint.
- **Migrations**: Alembic is configured and should be used for schema changes. `Base.metadata.create_all` in `app.py` is kept only as a safety net for dev.
- **Route order**: static routes (`/summary`, `/by-category`, `/by-month`) are declared **before** `/{id}` in each router to avoid FastAPI matching them as integer IDs.
- **Date parsing**: schemas use `@field_validator` to handle ISO 8601 strings (`2026-03-11T00:00:00.000Z`) and convert to `date`.
- **Numeric precision**: `Numeric(12, 2)` in models, serialized as `float` in schemas.
- **Investment enrichment**: `investments.py` calls yfinance at request time to compute `current_price`, `current_value`, `profit_loss`, `profit_loss_pct`.

## Data models

| Model | Table | Key fields |
|-------|-------|------------|
| `Account` | `accounts` | `name`, `initial_balance` |
| `Transaction` | `transactions` | `description`, `amount`, `category`, `date`, `is_income`, `account_id` |
| `Asset` | `assets` | `name`, `value`, `category`, `acquisition_date`, `is_initial`, `account_id` |
| `InvestmentInstrument` | `investment_instruments` | `symbol` (PK), `name`, `asset_type` |
| `Investment` | `investments` | `asset_symbol`, `quantity`, `purchase_price`, `purchase_date`, `source_account_id`, `is_initial` |

## API surface

### `/api/transactions`

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | List (filters: `month`, `year`, `category`, `is_income`, `account_id`) |
| POST | `/` | Create → 201 |
| GET | `/summary` | `total_income`, `total_expenses`, `balance`, `balance_with_investments`, `count` |
| GET | `/by-category` | Expenses grouped by category |
| GET | `/by-month` | Monthly income/expenses for a year |
| GET | `/{id}` | Single transaction |
| PUT | `/{id}` | Full update |
| DELETE | `/{id}` | Delete → 204 |

### `/api/accounts`

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | List accounts |
| POST | `/` | Create account |
| GET | `/{id}` | Get account |
| PUT | `/{id}` | Update account |
| DELETE | `/{id}` | Delete account |

### `/api/assets`

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | List assets |
| POST | `/` | Create asset |
| GET | `/{id}` | Get asset |
| PUT | `/{id}` | Update asset |
| DELETE | `/{id}` | Delete asset |

### `/api/investments`

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | List investments with live prices |
| POST | `/` | Create investment (upserts instrument) |
| GET | `/summary` | Portfolio totals: cost, current value, P&L |
| GET | `/by-symbol` | Aggregated positions per symbol |
| GET | `/instruments` | List tracked instruments |
| POST | `/instruments` | Create/upsert instrument |
| DELETE | `/{id}` | Delete investment |

## Transaction categories

Expenses: `comida`, `transporte`, `entretenimiento`, `salud`, `compras`, `servicios`, `educacion`, `otros`
Income: `ingreso` (`is_income=true`)

Asset categories: `inmueble`, `vehiculo`, `electronico`, `joya`, `arte`, `otro`

Investment types: `stock`, `etf`, `crypto`, `fund`
