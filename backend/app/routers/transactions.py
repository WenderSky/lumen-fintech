"""Router de transações (listagem com filtros + criação)."""
from __future__ import annotations

import re
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app import services
from app.database import get_db
from app.schemas import (
    TransacaoTipo,
    TransactionCreate,
    TransactionList,
    TransactionOut,
)

router = APIRouter(prefix="/api/transactions", tags=["transactions"])

MES_REGEX = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


@router.get(
    "",
    response_model=TransactionList,
    summary="Lista transações com filtros e paginação",
)
def get_transactions(
    db: Session = Depends(get_db),
    account_id: Optional[int] = Query(default=None, description="Filtra por conta"),
    tipo: Optional[TransacaoTipo] = Query(default=None, description="receita|despesa"),
    categoria: Optional[str] = Query(default=None, description="Filtra por categoria"),
    mes: Optional[str] = Query(default=None, description="Filtra por mês (YYYY-MM)"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> TransactionList:
    if mes is not None and not MES_REGEX.match(mes):
        raise HTTPException(status_code=422, detail="mes deve estar no formato YYYY-MM")

    total, itens = services.list_transactions(
        db,
        account_id=account_id,
        tipo=tipo,
        categoria=categoria,
        mes=mes,
        limit=limit,
        offset=offset,
    )
    return TransactionList(
        total=total,
        limit=limit,
        offset=offset,
        items=[TransactionOut.model_validate(t) for t in itens],
    )


@router.post(
    "",
    response_model=TransactionOut,
    status_code=status.HTTP_201_CREATED,
    summary="Cria uma transação e atualiza o saldo da conta",
)
def post_transaction(
    payload: TransactionCreate,
    db: Session = Depends(get_db),
) -> TransactionOut:
    try:
        transaction = services.create_transaction(
            db,
            account_id=payload.account_id,
            descricao=payload.descricao,
            valor=payload.valor,
            tipo=payload.tipo,
            categoria=payload.categoria,
            data=payload.data,
        )
    except services.AccountNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except services.InvalidAmount as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        )
    return TransactionOut.model_validate(transaction)
