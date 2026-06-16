"""Schemas Pydantic v2 (validação de entrada/saída).

Todo valor monetário usa Decimal. A serialização JSON mantém o número com
2 casas (json_encoders converte Decimal -> str pra não perder precisão).
"""
from __future__ import annotations

import datetime
from decimal import Decimal
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

AccountTipo = Literal["corrente", "poupanca", "carteira"]
TransacaoTipo = Literal["receita", "despesa"]


class AccountOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    tipo: AccountTipo
    saldo: Decimal


class TransactionCreate(BaseModel):
    account_id: int
    descricao: str = Field(min_length=1, max_length=255)
    valor: Decimal = Field(gt=Decimal("0"))
    tipo: TransacaoTipo
    categoria: str = Field(min_length=1, max_length=80)
    data: datetime.date

    @field_validator("valor")
    @classmethod
    def valor_positivo(cls, v: Decimal) -> Decimal:
        # Reforça a regra de negócio: dinheiro lançado precisa ser > 0.
        if v <= 0:
            raise ValueError("valor deve ser maior que zero")
        return v


class TransactionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    account_id: int
    descricao: str
    valor: Decimal
    tipo: TransacaoTipo
    categoria: str
    data: datetime.date
    criado_em: datetime.datetime


class TransactionList(BaseModel):
    """Resposta paginada da listagem de transações."""

    total: int
    limit: int
    offset: int
    items: list[TransactionOut]


class CategoriaResumo(BaseModel):
    categoria: str
    total: Decimal


class SummaryOut(BaseModel):
    mes: str
    total_receitas: Decimal
    total_despesas: Decimal
    saldo_mes: Decimal
    por_categoria: list[CategoriaResumo]


class HealthOut(BaseModel):
    status: str


# Aliases usados nos filtros de query (mantidos aqui pra reuso nos routers).
TransacaoTipoFiltro = Optional[TransacaoTipo]
