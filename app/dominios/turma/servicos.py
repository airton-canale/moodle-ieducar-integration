from __future__ import annotations

from app.dominios.turma.modelos import Turma
from app.dominios.turma.portas import DestinoDeCursos


def montar_idnumber(turma: Turma, prefixo: str) -> str:
    return f"{prefixo}{turma.id_ieducar}"


def garantir_curso(
    turma: Turma,
    destino: DestinoDeCursos,
    prefixo_idnumber: str,
    cache_idnumber_para_id: dict[str, int],
) -> int:
    idnumber = montar_idnumber(turma, prefixo_idnumber)
    if idnumber in cache_idnumber_para_id:
        return cache_idnumber_para_id[idnumber]
    existente = destino.buscar_por_idnumber(idnumber)
    if existente is not None:
        cache_idnumber_para_id[idnumber] = existente
        return existente
    novo = destino.criar(turma, idnumber)
    cache_idnumber_para_id[idnumber] = novo
    return novo
