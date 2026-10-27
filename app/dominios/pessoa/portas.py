from __future__ import annotations

from typing import Protocol

from app.dominios.pessoa.modelos import Pessoa


class FonteDePessoas(Protocol):
    def listar_pessoas(self, escola_id: int | None, ano: int) -> list[Pessoa]: ...


class DestinoDeUsuarios(Protocol):
    def buscar_por_idnumber(self, idnumber: str) -> int | None: ...
    def criar(self, pessoa: Pessoa, idnumber: str, username: str, email: str) -> int: ...
