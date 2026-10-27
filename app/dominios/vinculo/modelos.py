"""Vinculo = enturmacao + papel. Vocabulario i-Educar preservado para
facilitar rastreio com o legado."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from app.dominios.pessoa.modelos import Pessoa


class Papel(str, Enum):
    ALUNO = "aluno"
    PROFESSOR = "professor"


class Situacao(str, Enum):
    ATIVO = "ativo"
    INATIVO = "inativo"


@dataclass(frozen=True, slots=True)
class Vinculo:
    pessoa: Pessoa
    turma_id: int
    papel: Papel
    situacao: Situacao = Situacao.ATIVO
    matricula_id: int | None = None
