from __future__ import annotations

from typing import Protocol

from app.dominios.vinculo.modelos import Vinculo


class FonteDeVinculos(Protocol):
    def listar_vinculos(self, escola_id: int | None, ano: int) -> list[Vinculo]: ...


class DestinoDeInscricoes(Protocol):
    def inscrever(self, user_id: int, course_id: int, role_id: int) -> None: ...
    def desinscrever(self, user_id: int, course_id: int) -> None: ...
