"""Fixtures compartilhadas. SQLite in-memory + fakes para rodar o
pipeline inteiro sem docker."""
from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.database import Base
from app.dominios.sincronizacao import entidades  # noqa: F401
from app.dominios.sincronizacao.servicos import ParametrosFluxo, ServicoSincronizacao
from app.infraestrutura.ieducar.fake import IEducarFake
from app.infraestrutura.moodle.fake import MoodleFake


@pytest.fixture
def sessao() -> Session:
    engine = create_engine(
        "sqlite://",
        future=True,
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    Sess = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, future=True)
    sess = Sess()
    try:
        yield sess
    finally:
        sess.close()


@pytest.fixture
def ieducar_fake() -> IEducarFake:
    return IEducarFake()


@pytest.fixture
def moodle_fake() -> MoodleFake:
    return MoodleFake()


@pytest.fixture
def parametros() -> ParametrosFluxo:
    return ParametrosFluxo(
        escola_id=None,
        ano=2025,
        prefixo_turma="ieducar-turma-",
        prefixo_pessoa="ieducar-pessoa-",
        dominio_email="ieducar.local",
        role_aluno=5,
        role_professor=3,
    )


@pytest.fixture
def servico(sessao, ieducar_fake, moodle_fake) -> ServicoSincronizacao:
    from app.composicao import _AdaptadorCursos, _AdaptadorInscricoes, _AdaptadorUsuarios

    return ServicoSincronizacao(
        sessao=sessao,
        fonte_turmas=ieducar_fake,
        fonte_vinculos=ieducar_fake,
        destino_cursos=_AdaptadorCursos(moodle_fake),
        destino_usuarios=_AdaptadorUsuarios(moodle_fake),
        destino_inscricoes=_AdaptadorInscricoes(moodle_fake),
    )
