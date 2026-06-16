"""Camada de acesso a dados (repositories).

Responsabilidade única: traduzir intenções em queries SQLAlchemy.
Nenhuma regra de negócio / cálculo de dinheiro mora aqui — isso fica no service.
"""
from __future__ import annotations

import datetime
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Account, Transaction


def list_accounts(db: Session) -> list[Account]:
    return list(db.scalars(select(Account).order_by(Account.id)).all())


def get_account(db: Session, account_id: int) -> Optional[Account]:
    return db.get(Account, account_id)


def _month_bounds(mes: str) -> tuple[datetime.date, datetime.date]:
    """Converte 'YYYY-MM' no primeiro e no último dia do mês."""
    ano, mes_num = (int(p) for p in mes.split("-"))
    inicio = datetime.date(ano, mes_num, 1)
    # Primeiro dia do mês seguinte, depois recua 1 dia => último dia do mês atual.
    if mes_num == 12:
        prox = datetime.date(ano + 1, 1, 1)
    else:
        prox = datetime.date(ano, mes_num + 1, 1)
    fim = prox - datetime.timedelta(days=1)
    return inicio, fim


def query_transactions(
    db: Session,
    *,
    account_id: Optional[int] = None,
    tipo: Optional[str] = None,
    categoria: Optional[str] = None,
    mes: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[int, list[Transaction]]:
    """Lista transações com filtros, ordenadas por data desc, paginadas.

    Retorna (total_sem_paginacao, itens_da_pagina).
    """
    stmt = select(Transaction)
    if account_id is not None:
        stmt = stmt.where(Transaction.account_id == account_id)
    if tipo is not None:
        stmt = stmt.where(Transaction.tipo == tipo)
    if categoria is not None:
        stmt = stmt.where(Transaction.categoria == categoria)
    if mes is not None:
        inicio, fim = _month_bounds(mes)
        stmt = stmt.where(Transaction.data >= inicio, Transaction.data <= fim)

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0

    stmt = (
        stmt.order_by(Transaction.data.desc(), Transaction.id.desc())
        .limit(limit)
        .offset(offset)
    )
    itens = list(db.scalars(stmt).all())
    return total, itens


def transactions_in_month(db: Session, mes: str) -> list[Transaction]:
    """Todas as transações de um mês (sem paginação) — usado no resumo."""
    inicio, fim = _month_bounds(mes)
    stmt = (
        select(Transaction)
        .where(Transaction.data >= inicio, Transaction.data <= fim)
        .order_by(Transaction.data.asc(), Transaction.id.asc())
    )
    return list(db.scalars(stmt).all())


def add_transaction(db: Session, transaction: Transaction) -> Transaction:
    db.add(transaction)
    return transaction
