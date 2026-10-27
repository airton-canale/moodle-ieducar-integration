"""Composition root: unico lugar que conhece implementacoes concretas.
Dominios nao importam infra; a decisao http x fake entra aqui, lida da
configuracao."""
from __future__ import annotations

from functools import lru_cache
from typing import Any

from sqlalchemy.orm import Session

from app.config import configuracao
from app.dominios.sincronizacao.servicos import ServicoSincronizacao
from app.infraestrutura.http import ClienteHttp
from app.infraestrutura.ieducar.cliente import ClienteIEducar
from app.infraestrutura.ieducar.fake import IEducarFake
from app.infraestrutura.moodle.cliente import ClienteMoodle
from app.infraestrutura.moodle.fake import MoodleFake


@lru_cache(maxsize=1)
def construir_ieducar() -> Any:
    if configuracao.ieducar_cliente == "fake":
        return IEducarFake()
    http = ClienteHttp(configuracao.ieducar_base_url, timeout_seg=configuracao.ieducar_timeout_seg)
    return ClienteIEducar(http, configuracao.ieducar_access_key)


@lru_cache(maxsize=1)
def construir_moodle() -> Any:
    if configuracao.moodle_cliente == "fake":
        return MoodleFake()
    http = ClienteHttp(configuracao.moodle_base_url, timeout_seg=configuracao.moodle_timeout_seg)
    return ClienteMoodle(http, configuracao.moodle_token)


def construir_servico_sync(sessao: Session) -> ServicoSincronizacao:
    ieducar = construir_ieducar()
    moodle = construir_moodle()
    return ServicoSincronizacao(
        sessao=sessao,
        fonte_turmas=ieducar,
        fonte_vinculos=ieducar,
        destino_cursos=_AdaptadorCursos(moodle),
        destino_usuarios=_AdaptadorUsuarios(moodle),
        destino_inscricoes=_AdaptadorInscricoes(moodle),
    )


# Adaptadores finos: o Moodle (real ou fake) expoe uma superficie unica;
# cada adaptador apresenta apenas a porta que o dominio precisa.
class _AdaptadorCursos:
    def __init__(self, moodle: Any) -> None:
        self._m = moodle

    def buscar_por_idnumber(self, idnumber: str) -> int | None:
        return self._m.buscar_curso_por_idnumber(idnumber)

    def criar(self, turma: Any, idnumber: str) -> int:
        return self._m.criar_curso(turma, idnumber)


class _AdaptadorUsuarios:
    def __init__(self, moodle: Any) -> None:
        self._m = moodle

    def buscar_por_idnumber(self, idnumber: str) -> int | None:
        return self._m.buscar_usuario_por_idnumber(idnumber)

    def criar(self, pessoa: Any, idnumber: str, username: str, email: str) -> int:
        return self._m.criar_usuario(pessoa, idnumber, username, email)


class _AdaptadorInscricoes:
    def __init__(self, moodle: Any) -> None:
        self._m = moodle

    def inscrever(self, user_id: int, course_id: int, role_id: int) -> None:
        self._m.inscrever(user_id, course_id, role_id)

    def desinscrever(self, user_id: int, course_id: int) -> None:
        self._m.desinscrever(user_id, course_id)
