"""Pessoa como entidade pura do dominio. Frozen porque identidade vem do
i-Educar: mutar seria mascarar um bug de origem."""
from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Pessoa:
    id_ieducar: int
    nome: str
    email: str | None = None
    cpf: str | None = None

    @property
    def cpf_digitos(self) -> str | None:
        if not self.cpf:
            return None
        digitos = re.sub(r"\D", "", self.cpf)
        return digitos or None

    def dividir_nome(self) -> tuple[str, str]:
        """Moodle rejeita lastname vazio. Nome unico repete como sobrenome."""
        partes = [p for p in self.nome.strip().split() if p]
        if not partes:
            return ("Sem nome", "Sem nome")
        if len(partes) == 1:
            return (partes[0], partes[0])
        return (partes[0], " ".join(partes[1:]))
