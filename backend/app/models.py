"""Modelos ORM (SQLAlchemy 2.x).

Dinheiro é armazenado como Numeric(14, 2) para preservar precisão decimal exata
no banco. A camada de serviço sempre opera com Decimal quantizado em 2 casas.
"""
from __future__ import annotations

import datetime
from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

# Tipos de conta e de transação aceitos (validados também nos schemas Pydantic).
ACCOUNT_TYPES = ("corrente", "poupanca", "carteira")
TRANSACTION_TYPES = ("receita", "despesa")


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(120), nullable=False)
    tipo: Mapped[str] = mapped_column(String(20), nullable=False)
    # Numeric(14, 2) => até 12 dígitos inteiros + 2 decimais; mapeia pra Decimal.
    saldo: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), nullable=False, default=Decimal("0.00")
    )

    transactions: Mapped[list[Transaction]] = relationship(
        back_populates="account",
        cascade="all, delete-orphan",
    )


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(
        ForeignKey("accounts.id"), nullable=False, index=True
    )
    descricao: Mapped[str] = mapped_column(String(255), nullable=False)
    valor: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    tipo: Mapped[str] = mapped_column(String(20), nullable=False)
    categoria: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    data: Mapped[datetime.date] = mapped_column(nullable=False, index=True)
    criado_em: Mapped[datetime.datetime] = mapped_column(
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
    )

    account: Mapped[Account] = relationship(back_populates="transactions")
