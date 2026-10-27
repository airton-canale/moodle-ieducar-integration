"""Engine e factory de sessao. Separado para que testes possam injetar
um engine SQLite in-memory sem tocar nada mais."""
from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import configuracao


class Base(DeclarativeBase):
    pass


def construir_engine(url: str | None = None) -> Engine:
    url_final = url or configuracao.database_url
    # SQLite exige check_same_thread=False para rodar com o scheduler
    extra = {"connect_args": {"check_same_thread": False}} if url_final.startswith("sqlite") else {}
    return create_engine(url_final, future=True, **extra)


engine: Engine = construir_engine()
Sessao = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, future=True)


def obter_sessao() -> Iterator[Session]:
    sessao = Sessao()
    try:
        yield sessao
    finally:
        sessao.close()
