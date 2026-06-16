"""Camada de regras de negócio (services).

Aqui mora TODO o cálculo de dinheiro. Regras inegociáveis:
- dinheiro é sempre Decimal, nunca float;
- todo resultado monetário passa por `to_money` (quantize 2 casas, ROUND_HALF_UP);
- o saldo da conta e o resumo por categoria têm que bater ao centavo.
"""
from __future__ import annotations

import datetime
from collections import OrderedDict
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy.orm import Session

from app import repositories
from app.models import Account, Transaction

CENTAVO = Decimal("0.01")


class AccountNotFound(Exception):
    """Conta informada não existe."""


class InvalidAmount(Exception):
    """Valor monetário inválido (<= 0)."""


def to_money(value: Decimal | int | str) -> Decimal:
    """Normaliza qualquer valor pra Decimal com exatamente 2 casas decimais."""
    if not isinstance(value, Decimal):
        value = Decimal(str(value))
    return value.quantize(CENTAVO, rounding=ROUND_HALF_UP)


def list_accounts(db: Session) -> list[Account]:
    return repositories.list_accounts(db)


def list_transactions(
    db: Session,
    *,
    account_id: int | None = None,
    tipo: str | None = None,
    categoria: str | None = None,
    mes: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[int, list[Transaction]]:
    return repositories.query_transactions(
        db,
        account_id=account_id,
        tipo=tipo,
        categoria=categoria,
        mes=mes,
        limit=limit,
        offset=offset,
    )


def create_transaction(
    db: Session,
    *,
    account_id: int,
    descricao: str,
    valor: Decimal,
    tipo: str,
    categoria: str,
    data: datetime.date,
) -> Transaction:
    """Cria uma transação e atualiza o saldo da conta de forma consistente.

    Receita soma ao saldo, despesa subtrai. Tudo dentro de uma única
    transação de banco (commit atômico) pra nunca gravar lançamento sem
    refletir no saldo.
    """
    valor = to_money(valor)
    if valor <= 0:
        raise InvalidAmount("valor deve ser maior que zero")

    account = repositories.get_account(db, account_id)
    if account is None:
        raise AccountNotFound(f"conta {account_id} não encontrada")

    transaction = Transaction(
        account_id=account_id,
        descricao=descricao,
        valor=valor,
        tipo=tipo,
        categoria=categoria,
        data=data,
    )
    repositories.add_transaction(db, transaction)

    # Atualiza o saldo SEMPRE com Decimal quantizado (nunca float).
    saldo_atual = to_money(account.saldo)
    if tipo == "receita":
        account.saldo = to_money(saldo_atual + valor)
    else:  # despesa
        account.saldo = to_money(saldo_atual - valor)

    db.commit()
    db.refresh(transaction)
    return transaction


def build_summary(db: Session, mes: str) -> dict:
    """Resumo financeiro do mês, somando ao centavo com Decimal.

    Retorna total de receitas, de despesas, saldo do mês (receitas - despesas)
    e o total por categoria. A soma das categorias bate exatamente com a soma
    de receitas + despesas, porque tudo é acumulado em Decimal e quantizado
    apenas no final.
    """
    transacoes = repositories.transactions_in_month(db, mes)

    total_receitas = Decimal("0")
    total_despesas = Decimal("0")
    # OrderedDict preserva a ordem de primeira ocorrência das categorias.
    por_categoria: "OrderedDict[str, Decimal]" = OrderedDict()

    for t in transacoes:
        valor = to_money(t.valor)
        if t.tipo == "receita":
            total_receitas += valor
        else:
            total_despesas += valor
        por_categoria[t.categoria] = por_categoria.get(t.categoria, Decimal("0")) + valor

    total_receitas = to_money(total_receitas)
    total_despesas = to_money(total_despesas)
    saldo_mes = to_money(total_receitas - total_despesas)

    categorias = [
        {"categoria": cat, "total": to_money(total)}
        for cat, total in por_categoria.items()
    ]

    return {
        "mes": mes,
        "total_receitas": total_receitas,
        "total_despesas": total_despesas,
        "saldo_mes": saldo_mes,
        "por_categoria": categorias,
    }
