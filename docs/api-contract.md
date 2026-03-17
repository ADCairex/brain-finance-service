# API Contract — MisGastos Backend

Endpoints required by the frontend. Base URL configurable via `VITE_API_URL` (default: `http://localhost:8000`).

---

## Accounts

### GET `/api/accounts`
Lists all bank accounts.

**Response `200`:** Array of `Account` objects.

---

### GET `/api/accounts/{id}`
Gets an account by ID.

**Response `200`:** `Account` object.

---

### POST `/api/accounts`
Creates a new account.

**Request body:**
```json
{
  "name": "BBVA",
  "initial_balance": 2500.00
}
```

**Response `201`:** Created `Account` object.

---

### PUT `/api/accounts/{id}`
Updates account name and initial balance.

**Request body:** same schema as POST (both fields required).

**Response `200`:** Updated `Account` object.

---

### DELETE `/api/accounts/{id}`
Deletes an account. Associated transactions will have `account_id = null`.

**Response `204`:** No body.

---

## Transactions

### GET `/api/transactions`
List of transactions with optional filters.

**Query params:**
| Param | Type | Description |
|-------|------|-------------|
| `month` | int | Month (1–12) |
| `year` | int | Year |
| `category` | string | Exact category |
| `is_income` | bool | `true` = income, `false` = expenses |
| `account_id` | int | Filter by account |

**Response `200`:** Array of `Transaction` objects.

---

### GET `/api/transactions/{id}`
Gets a transaction by ID.

**Response `200`:** `Transaction` object.

---

### POST `/api/transactions`
Creates a new transaction.

**Request body:**
```json
{
  "description": "Lunch at restaurant",
  "amount": 150.00,
  "category": "comida",
  "date": "2026-03-11T00:00:00.000Z",
  "is_income": false,
  "notes": "With tip",
  "account_id": 1
}
```

> When `is_income` is `true`, the frontend sends `category: "ingreso"`.
> `account_id` is optional — if omitted, the transaction will not be linked to any account.

**Response `201`:** Created `Transaction` object.

---

### PUT `/api/transactions/{id}`
Updates an existing transaction.

**Request body:** same schema as POST.

**Response `200`:** Updated `Transaction` object.

---

### DELETE `/api/transactions/{id}`
Deletes a transaction.

**Response `204`:** No body.

---

## Aggregations

### GET `/api/transactions/summary`
Financial summary for the period.

**Query params:**
| Param | Type | Description |
|-------|------|-------------|
| `month` | int | Month (1–12) |
| `year` | int | Year |
| `account_id` | int | Limits the summary to one account. Without filter, sums all initial balances. When filtered by account, `total_invested` only includes investments whose `source_account_id` matches. |

**Response `200`:**
```json
{
  "total_income": 25000.00,
  "total_expenses": 10000.00,
  "total_invested": 5000.00,
  "total_assets_initial": 15000.00,
  "total_assets_acquired": 3000.00,
  "total_investments_initial": 8000.00,
  "initial_balance": 2500.00,
  "balance": 9500.00,
  "balance_with_investments": 17500.00,
  "count": 42
}
```

> `total_invested` — cost basis of investments with `is_initial: false` (new purchases; deducted from balance).
> `total_investments_initial` — cost basis of investments with `is_initial: true` (starting portfolio; **not** included in `balance`, only in `balance_with_investments`).
> `balance = initial_balance + total_assets_initial + total_income - total_expenses - total_invested - total_assets_acquired`
> `balance_with_investments = balance + total_investments_initial`

---

### GET `/api/transactions/by-category`
Expenses grouped by category (for pie/bar chart).

**Query params:** `month` (int), `year` (int), `account_id` (int)

**Response `200`:**
```json
[
  { "category": "comida", "total": 3500.00 },
  { "category": "transporte", "total": 1200.00 }
]
```

---

### GET `/api/transactions/by-month`
Monthly totals for the year (for line/bar chart).

**Query params:** `year` (int), `account_id` (int)

**Response `200`:**
```json
[
  { "month": 1, "income": 25000.00, "expenses": 10000.00 },
  { "month": 2, "income": 27000.00, "expenses": 12000.00 }
]
```

---

## Assets

Physical assets (vehicles, real estate, electronics, etc.) are managed independently from transactions.

- **Initial assets** (`is_initial: true`): starting net worth configuration. **Not counted as expenses** — they add to the balance as part of the starting net worth.
- **Acquired assets** (`is_initial: false`): new purchases. **Counted as expenses** — deducted from balance.

### GET `/api/assets`
Lists all assets.

**Response `200`:** Array of `Asset` objects.

---

### GET `/api/assets/{id}`
Gets an asset by ID.

**Response `200`:** `Asset` object.

---

### POST `/api/assets`
Registers a new asset.

**Request body:**
```json
{
  "name": "Honda Civic 2020",
  "value": 15000.00,
  "category": "vehiculo",
  "acquisition_date": "2020-06-01",
  "is_initial": true,
  "account_id": 1,
  "notes": "Initial configuration asset"
}
```

> `account_id` is optional.
> If `is_initial` is `true`, the asset adds to net worth without being counted as an expense.
> If `is_initial` is `false`, the value is deducted from the balance as an expense.

**Response `201`:** Created `Asset` object.

---

### PUT `/api/assets/{id}`
Updates an existing asset.

**Request body:** same schema as POST.

**Response `200`:** Updated `Asset` object.

---

### DELETE `/api/assets/{id}`
Deletes an asset.

**Response `204`:** No body.

---

## Investments

Current price is fetched in real time via Yahoo Finance (`yfinance`), supports stocks (`AAPL`), ETFs (`SPY`) and crypto (`BTC-USD`).

- **Initial investments** (`is_initial: true`): starting portfolio in the initial configuration. **Not deducted from balance** — they are part of the starting net worth.
- **New investments** (`is_initial: false`, default): new purchases. **Deducted from balance** (`total_invested`) but not counted as an expense.

### GET `/api/investments/by-symbol`
Investments grouped by symbol. Returns the combined return of all purchases of the same asset, plus the detail of each individual purchase.

**Query params:**
| Param | Type | Description |
|-------|------|-------------|
| `is_initial` | bool | `true` = initial portfolio only, `false` = new purchases only. Without filter, returns all. |
| `account_id` | int | Filter by the investment's source account. |

**Response `200`:**
```json
[
  {
    "asset_symbol": "AAPL",
    "asset_name": "Apple Inc.",
    "total_quantity": 15,
    "avg_purchase_price": 153.33,
    "cost_basis": 2300.00,
    "current_price": 178.50,
    "current_value": 2677.50,
    "profit_loss": 377.50,
    "profit_loss_pct": 16.41,
    "purchases": [
      {
        "id": 1,
        "quantity": 10,
        "purchase_price": 150.00,
        "purchase_date": "2026-01-01",
        "cost_basis": 1500.00,
        "current_price": 178.50,
        "current_value": 1785.00,
        "profit_loss": 285.00,
        "profit_loss_pct": 19.00
      },
      {
        "id": 2,
        "quantity": 5,
        "purchase_price": 160.00,
        "purchase_date": "2026-01-02",
        "cost_basis": 800.00,
        "current_price": 178.50,
        "current_value": 892.50,
        "profit_loss": 92.50,
        "profit_loss_pct": 11.56
      }
    ]
  }
]
```

> `avg_purchase_price = cost_basis_total / total_quantity`
> One Yahoo Finance call per symbol — all records with the same symbol share the same `current_price`.

---

### GET `/api/investments`
Lists all investments with return calculated in real time (one row per purchase, ungrouped).

**Response `200`:** Array of `Investment` objects enriched with current price.

---

### GET `/api/investments/summary`
Global portfolio summary.

**Query params:**
| Param | Type | Description |
|-------|------|-------------|
| `account_id` | int | Limits the summary to investments linked to an account. |

**Response `200`:**
```json
{
  "total_invested": 5000.00,
  "current_value": 6200.00,
  "profit_loss": 1200.00,
  "profit_loss_pct": 24.0
}
```

---

### GET `/api/investments/instruments`
Lists all registered financial instruments.

**Response `200`:** Array of `InvestmentInstrument` objects.

---

### POST `/api/investments/instruments`
Creates or updates a financial instrument (upsert by `symbol`).

**Request body:**
```json
{
  "symbol": "AAPL",
  "name": "Apple Inc.",
  "asset_type": "stock"
}
```

> `asset_type` valid values: `stock`, `etf`, `crypto`, `fund`.

**Response `201`:** Created or updated `InvestmentInstrument` object.

---

### POST `/api/investments`
Registers a new investment purchase. If the instrument (`asset_symbol`) does not exist, it is created automatically.

**Request body:**
```json
{
  "asset_symbol": "AAPL",
  "asset_name": "Apple Inc.",
  "asset_type": "stock",
  "quantity": 10,
  "purchase_price": 150.00,
  "purchase_date": "2026-01-15",
  "source_account_id": 1,
  "is_initial": false,
  "notes": "Initial purchase"
}
```

> `asset_name` and `asset_type` are used to create or update the instrument in `investment_instruments`. If the symbol already exists, its name and type are updated with the provided values.
> `source_account_id` is optional — indicates which account the investment funds come from.
> When `source_account_id` is specified, the investment cost (`quantity × purchase_price`) is attributed to that account:
> - In the **summary filtered by `account_id`**, `total_invested` only includes investments whose `source_account_id` matches the requested `account_id`.
> - The investment **does not generate an automatic transaction** — it does NOT appear as an expense in the account's transaction list.
> - The account balance is reduced by `total_invested` (existing formula), but the investment is only shown in the investments section, never as a transaction.
> `is_initial` (bool, default `false`): if `true`, the investment is **not** deducted from the balance (`total_invested`). Used when configuring the starting portfolio.

**Response `201`:** Created `Investment` object.

---

### DELETE `/api/investments/{id}`
Deletes an investment. When deleted, the source account's `total_invested` is automatically reduced (as the investment no longer exists). No refund transaction is generated.

**Response `204`:** No body.

---

## Models

### `Account`
```json
{
  "id": 1,
  "name": "BBVA",
  "initial_balance": 2500.00
}
```

### `Transaction`
```json
{
  "id": 1,
  "description": "Lunch at restaurant",
  "amount": 150.00,
  "category": "comida",
  "date": "2026-03-11",
  "is_income": false,
  "notes": "With tip",
  "account_id": 1
}
```

### `InvestmentInstrument`
```json
{
  "symbol": "AAPL",
  "name": "Apple Inc.",
  "asset_type": "stock"
}
```

### `Investment`
```json
{
  "id": 1,
  "asset_symbol": "AAPL",
  "asset_name": "Apple Inc.",
  "asset_type": "stock",
  "quantity": 10,
  "purchase_price": 150.00,
  "purchase_date": "2026-01-15",
  "cost_basis": 1500.00,
  "current_price": 178.50,
  "current_value": 1785.00,
  "profit_loss": 285.00,
  "profit_loss_pct": 19.0,
  "source_account_id": 1,
  "is_initial": false,
  "notes": "Initial purchase"
}
```

### `Asset`
```json
{
  "id": 1,
  "name": "Honda Civic 2020",
  "value": 15000.00,
  "category": "vehiculo",
  "acquisition_date": "2020-06-01",
  "is_initial": true,
  "account_id": 1,
  "notes": "Initial configuration asset"
}
```

### `InvestmentBySymbol`
```json
{
  "asset_symbol": "AAPL",
  "asset_name": "Apple Inc.",
  "total_quantity": 16.0,
  "avg_purchase_price": 157.87,
  "cost_basis": 2526.00,
  "current_price": 178.50,
  "current_value": 2856.00,
  "profit_loss": 330.00,
  "profit_loss_pct": 13.06,
  "purchases": [ ]
}
```

> Each object within `purchases` follows the `Investment` schema (includes `asset_type`).

### Valid categories (`Transaction`)
`comida` · `transporte` · `entretenimiento` · `salud` · `compras` · `servicios` · `educacion` · `otros` · `ingreso`

### Valid categories (`Asset`)
`vehiculo` · `inmueble` · `electronico` · `joya` · `otro`

---

## Errors

The frontend expects errors to have the `detail` field:
```json
{ "detail": "Human-readable error message" }
```

---

## Pending / Future improvements

The following `StatCards` in the dashboard have **hardcoded** values in the frontend and do not yet consume any endpoint:
- **Today's Expenses** — total expenses for the current day
- **This Week** — total expenses for the current week
- **This Month** — total expenses for the current month
- **Monthly Savings** — `total_income - total_expenses` for the month

Could be included in the `/summary` endpoint as additional fields or in a separate `/api/transactions/stats` endpoint.
