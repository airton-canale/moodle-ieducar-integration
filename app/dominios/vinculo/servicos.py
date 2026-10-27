from __future__ import annotations

from app.dominios.vinculo.modelos import Papel


def role_id_para_papel(papel: Papel, aluno_id: int, professor_id: int) -> int:
    return aluno_id if papel is Papel.ALUNO else professor_id
