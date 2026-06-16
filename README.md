# Lumen — Finanças pessoais (full-stack demo)

> ⚠️ **Aviso — código proprietário.** Este repositório é **somente para visualização** (demonstração de portfólio). **Proibido clonar, copiar, usar, modificar ou redistribuir**, no todo ou em parte, sem autorização por escrito. Todos os direitos reservados — ver [LICENSE](LICENSE).


Aplicação full-stack de finanças pessoais: contas, lançamentos de receita/despesa
e **resumo mensal por categoria**. O front-end é uma landing/dashboard estático e
o back-end é uma API REST profissional em FastAPI, organizada em camadas.

**🔗 Demo ao vivo:** https://devanshelltech.com.br/demos/landing-app/

---

## O que este projeto demonstra

- **Rigor monetário absoluto.** Todo valor de dinheiro é `Decimal`, nunca `float`.
  Os valores são quantizados em 2 casas (`ROUND_HALF_UP`) e armazenados como
  `Numeric(14, 2)` no banco. Saldo de conta e resumo por categoria **batem ao
  centavo** — há testes que somam centavos quebrados e conferem o `Decimal` exato.
- **Resumo financeiro por categoria.** O endpoint `/api/summary` agrega receitas,
  despesas, saldo do mês e o total por categoria; a soma das categorias é
  consistente com o total movimentado no mês.
- **Atualização consistente de saldo.** Criar uma transação atualiza o saldo da
  conta na mesma transação de banco (commit atômico): receita soma, despesa subtrai.
- **Arquitetura em camadas** clara e testável: `router → service → repository`,
  com o cálculo de dinheiro isolado na camada de serviço.

## Arquitetura

```
backend/
  app/
    main.py            # app FastAPI, CORS, metadata, /docs, /api/health
    database.py        # engine SQLAlchemy 2.x + SQLite, sessão por request
    models.py          # modelos ORM (Account, Transaction) — dinheiro em Numeric(14,2)
    schemas.py         # schemas Pydantic v2 (entrada/saída) com Decimal
    repositories.py    # acesso a dados (queries) — sem regra de negócio
    services.py        # regras de negócio + TODO o cálculo de dinheiro (Decimal)
    seed.py            # dados fictícios idempotentes (2 contas, ~20 transações)
    routers/
      accounts.py
      transactions.py
      summary.py
  tests/               # pytest + TestClient (banco em memória isolado)
  requirements.txt
frontend/
  index.html           # landing/dashboard estático
```

A regra de divisão de responsabilidades:

- **router** — recebe a requisição, valida formato, traduz erros em HTTP.
- **service** — regra de negócio e cálculo monetário (saldo, resumo).
- **repository** — apenas queries SQLAlchemy.

## Como rodar

```bash
cd backend
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# (opcional) popula o banco com dados de demonstração — idempotente
.venv/bin/python -m app.seed

# sobe a API com documentação em http://127.0.0.1:8000/docs
.venv/bin/uvicorn app.main:app --reload
```

Rodar os testes:

```bash
cd backend
.venv/bin/python -m pytest -q
```

O front-end é estático — basta abrir `frontend/index.html` no navegador.

## Endpoints

| Método | Rota                | Descrição                                                              |
| ------ | ------------------- | --------------------------------------------------------------------- |
| GET    | `/api/health`       | Health check → `{"status":"ok"}`                                      |
| GET    | `/api/accounts`     | Lista as contas com saldo                                              |
| GET    | `/api/transactions` | Lista transações; filtros `account_id`, `tipo`, `categoria`, `mes=YYYY-MM`; ordena por data desc; paginação (`limit`, `offset`) |
| POST   | `/api/transactions` | Cria transação (valida `valor > 0`, atualiza o saldo da conta) → `201` |
| GET    | `/api/summary`      | Resumo do mês: `total_receitas`, `total_despesas`, `saldo_mes`, `por_categoria[]` |

Documentação interativa (OpenAPI/Swagger) em `/docs`.

## Stack

Python · FastAPI · SQLAlchemy 2.x · SQLite · Pydantic v2 · pytest

---

© 2026 Wender Fernando Azevedo Falido · Devan Shell Tech — **Todos os direitos reservados.**
Código proprietário, ver [LICENSE](LICENSE).
