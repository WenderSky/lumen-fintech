"""Configuração do banco de dados (SQLAlchemy 2.x + SQLite)."""
from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

# Banco fica em backend/app.db (um nível acima deste pacote).
DB_PATH = Path(__file__).resolve().parent.parent / "app.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

# check_same_thread=False é necessário pro SQLite com FastAPI (threads do uvicorn).
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    """Base declarativa de todos os modelos ORM."""


def get_db() -> Generator[Session, None, None]:
    """Dependency do FastAPI: abre uma sessão por request e garante o fechamento."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Cria as tabelas (idempotente)."""
    # Import local pra registrar os modelos no metadata antes do create_all.
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
