"""Endpoints via TestClient. Troca a factory de sessao e os construtores
de infra por versoes de teste para isolar o processo de outros modulos."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker

from app import composicao
from app.database import Base
import app.database as database_mod
from app.dominios.sincronizacao import entidades  # noqa: F401
from app.infraestrutura.ieducar.fake import IEducarFake
from app.infraestrutura.moodle.fake import MoodleFake


@pytest.fixture
def cliente(monkeypatch) -> TestClient:
    engine = create_engine(
        "sqlite://",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    SessaoTeste = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, future=True)
    monkeypatch.setattr(database_mod, "engine", engine)
    monkeypatch.setattr(database_mod, "Sessao", SessaoTeste)

    ieducar = IEducarFake()
    moodle = MoodleFake()
    composicao.construir_ieducar.cache_clear()
    composicao.construir_moodle.cache_clear()
    monkeypatch.setattr(composicao, "construir_ieducar", lambda: ieducar)
    monkeypatch.setattr(composicao, "construir_moodle", lambda: moodle)
    # agendador off para o teste
    monkeypatch.setenv("AGENDADOR_HABILITADO", "false")

    from app.main import app

    def _obter_sessao_teste():
        s = SessaoTeste()
        try:
            yield s
        finally:
            s.close()

    from app.database import obter_sessao

    app.dependency_overrides[obter_sessao] = _obter_sessao_teste
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_saude_ok(cliente) -> None:
    r = cliente.get("/saude")
    assert r.status_code == 200
    assert r.json()["banco"] == "ok"


def test_sincronizacao_completa_endpoint(cliente) -> None:
    r = cliente.post("/sincronizacoes/completa")
    assert r.status_code == 200
    corpo = r.json()
    assert corpo["turmas"]["status"] == "concluida"
    assert corpo["vinculos"]["status"] == "concluida"


def test_listar_e_detalhar(cliente) -> None:
    cliente.post("/sincronizacoes/turmas")
    r = cliente.get("/sincronizacoes")
    assert r.status_code == 200
    lista = r.json()
    assert lista
    detalhe = cliente.get(f"/sincronizacoes/{lista[0]['id']}")
    assert detalhe.status_code == 200
    assert "falhas_detalhadas" in detalhe.json()
