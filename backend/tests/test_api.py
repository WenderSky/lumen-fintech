"""Testes da API Lumen (pytest + TestClient).

Foco no rigor monetário: saldo atualiza ao centavo, summary soma exato em Decimal.
"""
from __future__ import annotations

import datetime
from decimal import Decimal


def _hoje() -> datetime.date:
    return datetime.date.today()


def _mes_corrente() -> str:
    return _hoje().strftime("%Y-%m")


def _data_iso(dia: int = 10) -> str:
    hoje = _hoje()
    return datetime.date(hoje.year, hoje.month, min(dia, 28)).isoformat()


# --------------------------------------------------------------------------- #
# Health / contas
# --------------------------------------------------------------------------- #
def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_listar_contas(client):
    r = client.get("/api/accounts")
    assert r.status_code == 200
    contas = r.json()
    assert len(contas) == 2
    assert {c["tipo"] for c in contas} == {"corrente", "carteira"}


# --------------------------------------------------------------------------- #
# Criação de transação + saldo
# --------------------------------------------------------------------------- #
def test_criar_transacao_receita_atualiza_saldo(client):
    # Conta corrente começa em 1000.00 (ver conftest).
    payload = {
        "account_id": 1,
        "descricao": "Salário",
        "valor": "2500.50",
        "tipo": "receita",
        "categoria": "Salário",
        "data": _data_iso(5),
    }
    r = client.post("/api/transactions", json=payload)
    assert r.status_code == 201
    body = r.json()
    assert Decimal(str(body["valor"])) == Decimal("2500.50")

    contas = {c["id"]: c for c in client.get("/api/accounts").json()}
    # 1000.00 + 2500.50 = 3500.50 — exato ao centavo.
    assert Decimal(str(contas[1]["saldo"])) == Decimal("3500.50")


def test_criar_transacao_despesa_subtrai_saldo(client):
    payload = {
        "account_id": 1,
        "descricao": "Aluguel",
        "valor": "750.33",
        "tipo": "despesa",
        "categoria": "Moradia",
        "data": _data_iso(6),
    }
    r = client.post("/api/transactions", json=payload)
    assert r.status_code == 201

    contas = {c["id"]: c for c in client.get("/api/accounts").json()}
    # 1000.00 - 750.33 = 249.67
    assert Decimal(str(contas[1]["saldo"])) == Decimal("249.67")


def test_saldo_acumula_com_centavos_quebrados(client):
    # Três despesas com centavos que somam exatamente 100.00.
    for v in ("33.33", "33.33", "33.34"):
        r = client.post(
            "/api/transactions",
            json={
                "account_id": 2,  # carteira começa em 0.00
                "descricao": f"gasto {v}",
                "valor": v,
                "tipo": "despesa",
                "categoria": "Diversos",
                "data": _data_iso(7),
            },
        )
        assert r.status_code == 201

    contas = {c["id"]: c for c in client.get("/api/accounts").json()}
    # 0 - 100.00 = -100.00, sem erro de ponto flutuante.
    assert Decimal(str(contas[2]["saldo"])) == Decimal("-100.00")


def test_valor_invalido_zero_ou_negativo_retorna_422(client):
    for valor in ("0", "-10.00"):
        r = client.post(
            "/api/transactions",
            json={
                "account_id": 1,
                "descricao": "inválido",
                "valor": valor,
                "tipo": "despesa",
                "categoria": "Erro",
                "data": _data_iso(),
            },
        )
        assert r.status_code == 422, valor


def test_conta_inexistente_retorna_404(client):
    r = client.post(
        "/api/transactions",
        json={
            "account_id": 999,
            "descricao": "x",
            "valor": "10.00",
            "tipo": "receita",
            "categoria": "Outros",
            "data": _data_iso(),
        },
    )
    assert r.status_code == 404


# --------------------------------------------------------------------------- #
# Listagem + filtros + paginação
# --------------------------------------------------------------------------- #
def _criar_base(client):
    """Cria um conjunto conhecido de transações no mês corrente."""
    lancamentos = [
        ("Salário", "5000.00", "receita", "Salário", 5),
        ("Mercado", "300.00", "despesa", "Alimentação", 8),
        ("Restaurante", "120.00", "despesa", "Alimentação", 9),
        ("Luz", "200.00", "despesa", "Contas", 10),
    ]
    for descricao, valor, tipo, categoria, dia in lancamentos:
        r = client.post(
            "/api/transactions",
            json={
                "account_id": 1,
                "descricao": descricao,
                "valor": valor,
                "tipo": tipo,
                "categoria": categoria,
                "data": _data_iso(dia),
            },
        )
        assert r.status_code == 201


def test_filtro_por_tipo(client):
    _criar_base(client)
    r = client.get("/api/transactions", params={"tipo": "despesa"})
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 3
    assert all(it["tipo"] == "despesa" for it in body["items"])


def test_filtro_por_categoria(client):
    _criar_base(client)
    r = client.get("/api/transactions", params={"categoria": "Alimentação"})
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 2
    assert all(it["categoria"] == "Alimentação" for it in body["items"])


def test_filtro_por_mes(client):
    _criar_base(client)
    # Mês corrente tem 4 lançamentos.
    r = client.get("/api/transactions", params={"mes": _mes_corrente()})
    assert r.json()["total"] == 4

    # Um mês improvável no passado não tem nada.
    r2 = client.get("/api/transactions", params={"mes": "1990-01"})
    assert r2.json()["total"] == 0


def test_ordenacao_data_desc(client):
    _criar_base(client)
    body = client.get("/api/transactions").json()
    datas = [it["data"] for it in body["items"]]
    assert datas == sorted(datas, reverse=True)


def test_paginacao(client):
    _criar_base(client)
    r = client.get("/api/transactions", params={"limit": 2, "offset": 0})
    body = r.json()
    assert body["total"] == 4
    assert len(body["items"]) == 2
    assert body["limit"] == 2


def test_mes_formato_invalido_422(client):
    r = client.get("/api/transactions", params={"mes": "2026/01"})
    assert r.status_code == 422


# --------------------------------------------------------------------------- #
# Summary — o ponto forte: tem que bater ao centavo
# --------------------------------------------------------------------------- #
def test_summary_totais_e_por_categoria(client):
    _criar_base(client)
    r = client.get("/api/summary", params={"mes": _mes_corrente()})
    assert r.status_code == 200
    s = r.json()

    receitas = Decimal(str(s["total_receitas"]))
    despesas = Decimal(str(s["total_despesas"]))
    saldo = Decimal(str(s["saldo_mes"]))

    assert receitas == Decimal("5000.00")
    assert despesas == Decimal("620.00")  # 300 + 120 + 200
    assert saldo == Decimal("4380.00")  # 5000 - 620

    por_cat = {c["categoria"]: Decimal(str(c["total"])) for c in s["por_categoria"]}
    assert por_cat["Salário"] == Decimal("5000.00")
    assert por_cat["Alimentação"] == Decimal("420.00")  # 300 + 120
    assert por_cat["Contas"] == Decimal("200.00")


def test_summary_decimal_exato_com_centavos_quebrados(client):
    # Valores escolhidos pra estourar erro de float se alguém usar float.
    # 0.10 + 0.20 + 0.30 + ... etc — somamos algo que float erraria.
    valores = ["10.10", "20.20", "30.30", "0.07", "0.03"]  # soma = 60.70
    for i, v in enumerate(valores):
        r = client.post(
            "/api/transactions",
            json={
                "account_id": 1,
                "descricao": f"despesa {i}",
                "valor": v,
                "tipo": "despesa",
                "categoria": "Precisao",
                "data": _data_iso(10),
            },
        )
        assert r.status_code == 201

    s = client.get("/api/summary", params={"mes": _mes_corrente()}).json()

    esperado = sum((Decimal(v) for v in valores), Decimal("0")).quantize(Decimal("0.01"))
    assert esperado == Decimal("60.70")

    despesas = Decimal(str(s["total_despesas"]))
    assert despesas == esperado  # bate ao centavo, sem desvio de float

    por_cat = {c["categoria"]: Decimal(str(c["total"])) for c in s["por_categoria"]}
    assert por_cat["Precisao"] == Decimal("60.70")

    # A soma das categorias tem que igualar receitas + despesas do mês.
    soma_categorias = sum(
        (Decimal(str(c["total"])) for c in s["por_categoria"]), Decimal("0")
    )
    total_movimentado = Decimal(str(s["total_receitas"])) + Decimal(
        str(s["total_despesas"])
    )
    assert soma_categorias == total_movimentado
