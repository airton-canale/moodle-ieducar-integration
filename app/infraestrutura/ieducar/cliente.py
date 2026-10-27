"""Cliente HTTP real do i-Educar. Fala com o modulo legado em
/module/Api/, que exige access_key em todas as chamadas e devolve JSON
com `any_error_msg` quando falha logicamente (status 200)."""
from __future__ import annotations

from typing import Any

from app.dominios.pessoa.modelos import Pessoa
from app.dominios.turma.modelos import Turma
from app.dominios.vinculo.modelos import Vinculo
from app.infraestrutura.erros import ErroIEducar
from app.infraestrutura.http import ClienteHttp
from app.infraestrutura.ieducar.tradutor import (
    traduzir_enturmacao,
    traduzir_pessoa,
    traduzir_turma,
)


class ClienteIEducar:
    """Agregacao das tres fontes. Composicao injeta como as tres portas."""

    def __init__(self, http: ClienteHttp, access_key: str) -> None:
        if not access_key:
            raise ErroIEducar("IEDUCAR_ACCESS_KEY nao configurada")
        self._http = http
        self._access_key = access_key

    def _get(self, modulo: str, resource: str, params: dict[str, Any]) -> dict[str, Any]:
        base: dict[str, Any] = {"oper": "get", "resource": resource, "access_key": self._access_key}
        base.update({k: v for k, v in params.items() if v is not None})
        resposta = self._http.get(f"/module/Api/{modulo}", params=base)
        try:
            corpo = resposta.json()
        except ValueError as exc:
            raise ErroIEducar(f"Resposta nao-JSON de {modulo}/{resource}") from exc
        erro = corpo.get("any_error_msg")
        if erro:
            raise ErroIEducar(f"{modulo}/{resource}: {erro}")
        return corpo

    def listar_turmas(self, escola_id: int | None, ano: int) -> list[Turma]:
        corpo = self._get(
            "Turma",
            "turmas-por-escola",
            {"escola": escola_id, "ano": ano, "instituicao_id": 1},
        )
        resultado: list[Turma] = []
        for bruto in corpo.get("turmas", []):
            t = traduzir_turma(bruto, ano)
            if t is not None:
                resultado.append(t)
        return resultado

    def _indice_pessoas_por_matricula(self, escola_id: int | None, ano: int) -> dict[int, Pessoa]:
        """matricula_id -> Pessoa. enturmacoes referenciam matricula, nao aluno."""
        corpo = self._get(
            "Aluno",
            "alunos-matriculados",
            {"escola_id": escola_id, "ano": ano, "instituicao_id": 1},
        )
        indice: dict[int, Pessoa] = {}
        for bruto in corpo.get("alunos", corpo.get("students", [])):
            pessoa = traduzir_pessoa(bruto)
            if pessoa is None:
                continue
            matricula_id = bruto.get("matricula_id") or bruto.get("ref_cod_matricula")
            if matricula_id is None:
                continue
            try:
                indice[int(matricula_id)] = pessoa
            except (TypeError, ValueError):
                continue
        return indice

    def listar_pessoas(self, escola_id: int | None, ano: int) -> list[Pessoa]:
        return list(self._indice_pessoas_por_matricula(escola_id, ano).values())

    def listar_vinculos(self, escola_id: int | None, ano: int) -> list[Vinculo]:
        indice = self._indice_pessoas_por_matricula(escola_id, ano)
        corpo = self._get(
            "Matricula",
            "movimentacao-enturmacao",
            {"escola": escola_id, "ano": ano},
        )
        vinculos: list[Vinculo] = []
        for bruto in corpo.get("enturmacoes", corpo.get("movimentacoes", [])):
            matricula_id = bruto.get("matricula_id") or bruto.get("ref_cod_matricula")
            if matricula_id is None:
                continue
            try:
                pessoa = indice.get(int(matricula_id))
            except (TypeError, ValueError):
                continue
            if pessoa is None:
                continue
            v = traduzir_enturmacao(bruto, pessoa)
            if v is not None:
                vinculos.append(v)
        return vinculos
