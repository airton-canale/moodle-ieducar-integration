"""Turma pura. Campos de escola/curso/serie entram no fullname/shortname
porque Moodle nao expoe nativamente a hierarquia escolar do i-Educar."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Turma:
    id_ieducar: int
    nome: str
    ano: int
    escola_id: int | None = None
    escola_nome: str | None = None
    curso_nome: str | None = None
    serie_nome: str | None = None
    turno: str | None = None

    def fullname(self) -> str:
        pedacos = [p for p in (self.escola_nome, self.curso_nome, self.serie_nome, self.nome) if p]
        base = " / ".join(pedacos) if pedacos else self.nome
        return f"{base} ({self.ano})"

    def shortname(self) -> str:
        return f"{self.id_ieducar}-{self.ano}"
