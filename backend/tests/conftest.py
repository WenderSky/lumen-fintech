"""Fixtures de teste: banco SQLite em memória isolado + TestClient.

Cada teste roda contra um banco limpo, com 2 contas pré-criadas, sem tocar
no app.db real.
"""
from __future__ import annotations

from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import Account


@pytest.fixture()
def db_session():
    # Banco em memória; StaticPool mantém a mesma conexão entre threads.
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    db = TestingSession()
    # Duas contas fixas pros testes.
    corrente = Account(nome="Conta Corrente", tipo="corrente", saldo=Decimal("1000.00"))
    carteira = Account(nome="Carteira", tipo="carteira", saldo=Decimal("0.00"))
    db.add_all([corrente, carteira])
    db.commit()

    try:
        yield db, TestingSession
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture()
def client(db_session):
    _, TestingSession = db_session

    def override_get_db():
        session = TestingSession()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
