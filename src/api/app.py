from fastapi import FastAPI

from .endpoints.accounts import router as accounts_router
from .endpoints.assets import router as assets_router
from .endpoints.investments import router as investments_router
from .endpoints.transactions import router as transactions_router
from .endpoints.transfers import router as transfers_router

app = FastAPI(title="MisGastos API", version="0.1.0")

app.include_router(transactions_router)
app.include_router(accounts_router)
app.include_router(assets_router)
app.include_router(investments_router)
app.include_router(transfers_router)
