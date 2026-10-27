from __future__ import annotations

from typing import Protocol

from app.dominios.turma.modelos import Turma


class FonteDeTurmas(Protocol):
    def listar_turmas(self, escola_id: int | None, ano: int) -> list[Turma]: ...


class DestinoDeCursos(Protocol):
    def buscar_por_idnumber(self, idnumber: str) -> int | None: ...
    def criar(self, turma: Turma, idnumber: str) -> int: ...
