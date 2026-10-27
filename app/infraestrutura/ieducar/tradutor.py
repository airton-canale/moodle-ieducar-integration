"""Tradutor payload -> modelo de dominio. Tolerante a nomes de campos
variantes porque o i-Educar renomeou colunas entre versoes."""
from __future__ import annotations

from typing import Any

from app.dominios.pessoa.modelos import Pessoa
from app.dominios.turma.modelos import Turma
from app.dominios.vinculo.modelos import Papel, Situacao, Vinculo


def _primeiro(dicio: dict[str, Any], chaves: tuple[str, ...], padrao: Any = None) -> Any:
    for chave in chaves:
        if chave in dicio and dicio[chave] not in (None, ""):
            return dicio[chave]
    return padrao


def _para_int(valor: Any) -> int | None:
    if valor in (None, "", False):
        return None
    try:
        return int(valor)
    except (TypeError, ValueError):
        return None


def traduzir_turma(bruto: dict[str, Any], ano_padrao: int) -> Turma | None:
    id_ = _para_int(_primeiro(bruto, ("cod_turma", "turma_id", "id")))
    if id_ is None:
        return None
    return Turma(
        id_ieducar=id_,
        nome=str(_primeiro(bruto, ("nm_turma", "nome", "turma_nome"), "")).strip() or f"Turma {id_}",
        ano=_para_int(_primeiro(bruto, ("ano", "ano_letivo"))) or ano_padrao,
        escola_id=_para_int(_primeiro(bruto, ("ref_cod_escola", "escola_id", "cod_escola"))),
        escola_nome=_primeiro(bruto, ("escola_nome", "nm_escola", "nome_escola")),
        curso_nome=_primeiro(bruto, ("curso_nome", "nm_curso")),
        serie_nome=_primeiro(bruto, ("serie_nome", "nm_serie")),
        turno=_primeiro(bruto, ("turno", "turma_turno_id")),
    )


def traduzir_pessoa(bruto: dict[str, Any]) -> Pessoa | None:
    id_ = _para_int(_primeiro(bruto, ("cod_aluno", "aluno_id", "id", "pessoa_id")))
    if id_ is None:
        return None
    nome = str(_primeiro(bruto, ("nome", "nm_aluno", "nome_aluno", "pessoa_nome"), "")).strip()
    if not nome:
        nome = f"Pessoa {id_}"
    return Pessoa(
        id_ieducar=id_,
        nome=nome,
        email=_primeiro(bruto, ("email", "email_aluno")),
        cpf=_primeiro(bruto, ("cpf", "cpf_aluno")),
    )


def traduzir_enturmacao(bruto: dict[str, Any], pessoa: Pessoa) -> Vinculo | None:
    turma_id = _para_int(_primeiro(bruto, ("turma_id", "ref_cod_turma", "cod_turma")))
    if turma_id is None:
        return None
    situacao_bruta = str(_primeiro(bruto, ("ativo", "situacao"), 1))
    inativo = situacao_bruta in ("0", "false", "False", "inativo", "0.0")
    papel_str = str(_primeiro(bruto, ("papel", "funcao", "tipo"), "aluno")).lower()
    papel = Papel.PROFESSOR if "prof" in papel_str or "doc" in papel_str else Papel.ALUNO
    return Vinculo(
        pessoa=pessoa,
        turma_id=turma_id,
        papel=papel,
        situacao=Situacao.INATIVO if inativo else Situacao.ATIVO,
        matricula_id=_para_int(_primeiro(bruto, ("matricula_id", "ref_cod_matricula"))),
    )
