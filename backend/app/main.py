"""Aplicação FastAPI — Lumen (finanças pessoais).

Sobe a API REST, registra os routers e configura CORS e a documentação /docs.
"""
from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.routers import accounts, summary, transactions
from app.schemas import HealthOut

tags_metadata = [
    {"name": "accounts", "description": "Contas do usuário (corrente, poupança, carteira)."},
    {"name": "transactions", "description": "Lançamentos de receita e despesa."},
    {"name": "summary", "description": "Resumo financeiro mensal e por categoria."},
    {"name": "health", "description": "Verificação de saúde da API."},
]

@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    # Garante as tabelas ao subir a aplicação.
    init_db()
    yield


app = FastAPI(
    title="Lumen API",
    description=(
        "API de finanças pessoais — contas, transações e resumo por categoria. "
        "Todo valor monetário é tratado com Decimal e quantizado em 2 casas."
    ),
    version="1.0.0",
    openapi_tags=tags_metadata,
    lifespan=lifespan,
)

# CORS liberado pra demo (front estático consome a API de qualquer origem).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health", response_model=HealthOut, tags=["health"], summary="Health check")
def health() -> HealthOut:
    return HealthOut(status="ok")


app.include_router(accounts.router)
app.include_router(transactions.router)
app.include_router(summary.router)
