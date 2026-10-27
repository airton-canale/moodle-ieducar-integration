"""Regras de aterrissagem de uma Pessoa no Moodle. Nunca envia CPF,
filiacao ou endereco (minimizacao, LGPD)."""
from __future__ import annotations

from app.dominios.pessoa.modelos import Pessoa
from app.dominios.pessoa.portas import DestinoDeUsuarios


def montar_idnumber(pessoa: Pessoa, prefixo: str) -> str:
    return f"{prefixo}{pessoa.id_ieducar}"


def montar_username(pessoa: Pessoa) -> str:
    cpf = pessoa.cpf_digitos
    if cpf:
        return cpf
    return f"ieducar.pessoa.{pessoa.id_ieducar}"


def montar_email(pessoa: Pessoa, dominio_sintetico: str) -> str:
    if pessoa.email and "@" in pessoa.email:
        return pessoa.email.strip().lower()
    return f"ieducar-pessoa-{pessoa.id_ieducar}@{dominio_sintetico}"


def garantir_usuario(
    pessoa: Pessoa,
    destino: DestinoDeUsuarios,
    prefixo_idnumber: str,
    dominio_email: str,
    cache_idnumber_para_id: dict[str, int],
) -> int:
    """Retorna o userid Moodle, criando se necessario. Idempotente."""
    idnumber = montar_idnumber(pessoa, prefixo_idnumber)
    if idnumber in cache_idnumber_para_id:
        return cache_idnumber_para_id[idnumber]

    existente = destino.buscar_por_idnumber(idnumber)
    if existente is not None:
        cache_idnumber_para_id[idnumber] = existente
        return existente

    username = montar_username(pessoa)
    email = montar_email(pessoa, dominio_email)
    novo = destino.criar(pessoa, idnumber, username, email)
    cache_idnumber_para_id[idnumber] = novo
    return novo
