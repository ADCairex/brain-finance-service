# brain-finance-service

Backend microservice for the **MisGastos** personal finance platform. Exposes a REST API for managing transactions, accounts, assets, and investment portfolios with real-time market data.

## Tech stack

- **Python 3.11+** · **FastAPI** · **SQLAlchemy 2.0 (sync)** · **PostgreSQL 17**
- **Alembic** for migrations · **yfinance** for live stock prices · **uv** for dependency management

## Quick start

```bash
# 1. Start the database
docker compose up -d

# 2. Install dependencies
uv sync

# 3. Configure environment
cp .env.example .env   # edit DATABASE_URL if needed

# 4. Apply migrations
make migrate

# 5. (Optional) Seed with sample data
make populate-db

# 6. Start dev server
make run   # → uv run python -m uvicorn src.api.app:app --reload --port 8000
# API available at http://localhost:8000
# Docs at http://localhost:8000/docs
```

pgAdmin is available at `http://localhost:5050` (admin@admin.com / admin).

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql://postgres:postgres@localhost:5432/misgastos` | PostgreSQL connection string |

## API overview

Base URL: `http://localhost:8000`

### Transactions — `/api/transactions`

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | List transactions. Filters: `month`, `year`, `category`, `is_income`, `account_id` |
| POST | `/` | Create transaction |
| GET | `/summary` | Aggregated totals: income, expenses, balance, investments |
| GET | `/by-category` | Expense breakdown by category |
| GET | `/by-month` | Monthly income/expenses for a given year |
| GET | `/{id}` | Get transaction |
| PUT | `/{id}` | Update transaction |
| DELETE | `/{id}` | Delete transaction |

### Accounts — `/api/accounts`

Standard CRUD. Accounts group transactions and investments. Each account has an `initial_balance` that feeds into the net balance calculation.

### Assets — `/api/assets`

Track physical or non-market assets (real estate, vehicles, electronics, etc.). Assets marked `is_initial=true` represent net worth starting point.

### Investments — `/api/investments`

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | List all purchases with live prices (via yfinance) |
| POST | `/` | Record a purchase (auto-creates instrument) |
| GET | `/summary` | Portfolio totals: cost basis, current value, P&L |
| GET | `/by-symbol` | Aggregate positions per ticker |
| GET | `/instruments` | List tracked instruments |
| POST | `/instruments` | Create/upsert instrument |
| DELETE | `/{id}` | Delete a purchase |

## Data model

```
accounts ──┬── transactions
           ├── assets
           └── investments ── investment_instruments
```

- **Account**: container with an initial balance
- **Transaction**: income or expense, categorized, linked to an account
- **Asset**: non-market asset with a fixed value
- **InvestmentInstrument**: ticker metadata (symbol, name, type)
- **Investment**: individual purchase of an instrument, with quantity and price

## Categories

**Expense categories:** `comida`, `transporte`, `entretenimiento`, `salud`, `compras`, `servicios`, `educacion`, `otros`

**Income:** `ingreso` (set `is_income=true`)

**Asset types:** `inmueble`, `vehiculo`, `electronico`, `joya`, `arte`, `otro`

**Investment types:** `stock`, `etf`, `crypto`, `fund`

## Useful commands

```bash
make run                        # Start dev server (port 8000)
make migrate                    # Apply pending migrations
make migration msg="add field"  # Generate new migration
make populate-db                # Load seed data
make reset-db                   # Reset DB to baseline
make backup-db                  # Dump current data to data/backup.sql
```

## Project structure

```
src/api/
├── app.py               # FastAPI app, CORS, router registration
├── config.py            # Settings from .env
├── database.py          # Engine, session, Base, get_db
├── models.py            # ORM models
├── schemas.py           # Pydantic request/response schemas
└── endpoints/
    ├── transactions.py
    ├── accounts.py
    ├── assets.py
    └── investments.py

alembic/                 # Migration environment
data/                    # SQL seed, reset, and backup scripts
docs/                    # api-contract.md, db-schema.svg
docker-compose.yml       # PostgreSQL + pgAdmin
Makefile                 # Dev shortcuts
```

## Related services

| Service | Repo | Default port |
|---------|------|-------------|
| brain-frontend | `../brain-frontend` | 5173 |
| brain-finance-service (this) | — | 8000 |
