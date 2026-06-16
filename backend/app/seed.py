"""Popula o banco com dados fictícios pra demonstração.

Idempotente: se já houver contas, não duplica nada. Cria ~2 contas e ~20
transações em categorias variadas, distribuídas no mês corrente e no anterior.
O saldo de cada conta é recalculado a partir das transações pra ficar coerente.

Uso:  python -m app.seed
"""
from __future__ import annotations

import datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import SessionLocal, init_db
from app.models import Account, Transaction
from app.services import to_money


def _month_ref(offset: int) -> tuple[int, int]:
    """Retorna (ano, mes) com `offset` meses atrás a partir de hoje."""
    hoje = datetime.date.today()
    ano = hoje.year
    mes = hoje.month - offset
    while mes <= 0:
        mes += 12
        ano -= 1
    return ano, mes


def _d(ano: int, mes: int, dia: int) -> datetime.date:
    # Garante um dia válido pro mês (clampa pra não estourar).
    dia = min(dia, 28)
    return datetime.date(ano, mes, dia)


def seed(db: Session) -> None:
    if db.scalar(select(Account).limit(1)) is not None:
        print("Banco já populado — seed ignorado (idempotente).")
        return

    corrente = Account(nome="Conta Corrente", tipo="corrente", saldo=Decimal("0.00"))
    carteira = Account(nome="Carteira", tipo="carteira", saldo=Decimal("0.00"))
    db.add_all([corrente, carteira])
    db.flush()  # gera os IDs

    a_ano, a_mes = _month_ref(0)  # mês corrente
    b_ano, b_mes = _month_ref(1)  # mês anterior

    # (account, descricao, valor, tipo, categoria, data)
    dados = [
        # --- mês corrente ---
        (corrente, "Salário", "5200.00", "receita", "Salário", _d(a_ano, a_mes, 5)),
        (corrente, "Freelance landing page", "1450.00", "receita", "Freelance", _d(a_ano, a_mes, 12)),
        (corrente, "Aluguel", "1800.00", "despesa", "Moradia", _d(a_ano, a_mes, 6)),
        (corrente, "Supermercado", "742.35", "despesa", "Alimentação", _d(a_ano, a_mes, 8)),
        (carteira, "Almoço restaurante", "48.90", "despesa", "Alimentação", _d(a_ano, a_mes, 9)),
        (corrente, "Conta de luz", "189.47", "despesa", "Contas", _d(a_ano, a_mes, 10)),
        (corrente, "Internet", "119.90", "despesa", "Contas", _d(a_ano, a_mes, 10)),
        (carteira, "Uber", "27.50", "despesa", "Transporte", _d(a_ano, a_mes, 11)),
        (corrente, "Streaming", "39.90", "despesa", "Lazer", _d(a_ano, a_mes, 14)),
        (corrente, "Academia", "99.00", "despesa", "Saúde", _d(a_ano, a_mes, 15)),
        (carteira, "Cinema", "64.00", "despesa", "Lazer", _d(a_ano, a_mes, 16)),
        # --- mês anterior ---
        (corrente, "Salário", "5200.00", "receita", "Salário", _d(b_ano, b_mes, 5)),
        (corrente, "Venda usados", "320.00", "receita", "Outros", _d(b_ano, b_mes, 20)),
        (corrente, "Aluguel", "1800.00", "despesa", "Moradia", _d(b_ano, b_mes, 6)),
        (corrente, "Supermercado", "688.12", "despesa", "Alimentação", _d(b_ano, b_mes, 7)),
        (corrente, "Conta de luz", "176.33", "despesa", "Contas", _d(b_ano, b_mes, 10)),
        (corrente, "Internet", "119.90", "despesa", "Contas", _d(b_ano, b_mes, 10)),
        (carteira, "Posto de gasolina", "250.00", "despesa", "Transporte", _d(b_ano, b_mes, 12)),
        (corrente, "Farmácia", "84.70", "despesa", "Saúde", _d(b_ano, b_mes, 18)),
        (carteira, "Presente aniversário", "150.00", "despesa", "Lazer", _d(b_ano, b_mes, 22)),
    ]

    for account, descricao, valor, tipo, categoria, data in dados:
        v = to_money(valor)
        db.add(
            Transaction(
                account_id=account.id,
                descricao=descricao,
                valor=v,
                tipo=tipo,
                categoria=categoria,
                data=data,
            )
        )
        # Atualiza saldo da conta de forma consistente (mesma regra do service).
        if tipo == "receita":
            account.saldo = to_money(to_money(account.saldo) + v)
        else:
            account.saldo = to_money(to_money(account.saldo) - v)

    db.commit()
    print(f"Seed concluído: 2 contas e {len(dados)} transações criadas.")


def main() -> None:
    init_db()
    db = SessionLocal()
    try:
        seed(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()
