"""Router FastAPI. Endpoints sao sincronos e devolvem o resumo da
execucao, conforme requisito."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.composicao import construir_servico_sync
from app.config import configuracao
from app.database import obter_sessao
from app.dominios.sincronizacao.entidades import ExecucaoSync, FalhaSync
from app.dominios.sincronizacao.repositorios import ExecucaoRepo
from app.dominios.sincronizacao.servicos import ParametrosFluxo

roteador = APIRouter()


def _parametros(escola_id: int | None, ano: int | None) -> ParametrosFluxo:
    return ParametrosFluxo(
        escola_id=escola_id if escola_id is not None else configuracao.escola_id_padrao,
        ano=ano if ano is not None else configuracao.ano_padrao,
        prefixo_turma=configuracao.prefixo_idnumber_turma,
        prefixo_pessoa=configuracao.prefixo_idnumber_pessoa,
        dominio_email=configuracao.dominio_email_sintetico,
        role_aluno=configuracao.moodle_role_aluno,
        role_professor=configuracao.moodle_role_professor,
    )


class ResumoExecucao(BaseModel):
    id: int
    fluxo: str
    escola_id: int | None
    ano: int
    status: str
    iniciada_em: datetime
    finalizada_em: datetime | None
    processados: int
    criados: int
    reaproveitados: int
    falhas: int
    mensagem: str | None = None

    @classmethod
    def de_entidade(cls, e: ExecucaoSync) -> "ResumoExecucao":
        return cls(
            id=e.id,
            fluxo=e.fluxo,
            escola_id=e.escola_id,
            ano=e.ano,
            status=e.status,
            iniciada_em=e.iniciada_em,
            finalizada_em=e.finalizada_em,
            processados=e.processados,
            criados=e.criados,
            reaproveitados=e.reaproveitados,
            falhas=e.falhas,
            mensagem=e.mensagem,
        )


class DetalheFalha(BaseModel):
    tipo: str
    id_ieducar: int | None
    descricao: str

    @classmethod
    def de_entidade(cls, f: FalhaSync) -> "DetalheFalha":
        return cls(tipo=f.tipo, id_ieducar=f.id_ieducar, descricao=f.descricao)


class DetalheExecucao(ResumoExecucao):
    falhas_detalhadas: list[DetalheFalha] = []


@roteador.post("/sincronizacoes/turmas", response_model=ResumoExecucao)
def sincronizar_turmas(
    escola_id: int | None = None, ano: int | None = None, sessao: Session = Depends(obter_sessao)
) -> ResumoExecucao:
    servico = construir_servico_sync(sessao)
    exec_ = servico.sincronizar_turmas(_parametros(escola_id, ano))
    return ResumoExecucao.de_entidade(exec_)


@roteador.post("/sincronizacoes/vinculos", response_model=ResumoExecucao)
def sincronizar_vinculos(
    escola_id: int | None = None, ano: int | None = None, sessao: Session = Depends(obter_sessao)
) -> ResumoExecucao:
    servico = construir_servico_sync(sessao)
    exec_ = servico.sincronizar_vinculos(_parametros(escola_id, ano))
    return ResumoExecucao.de_entidade(exec_)


class ResumoCompleto(BaseModel):
    turmas: ResumoExecucao
    vinculos: ResumoExecucao


@roteador.post("/sincronizacoes/completa", response_model=ResumoCompleto)
def sincronizar_completa(
    escola_id: int | None = None, ano: int | None = None, sessao: Session = Depends(obter_sessao)
) -> ResumoCompleto:
    servico = construir_servico_sync(sessao)
    ex_t, ex_v = servico.sincronizar_completa(_parametros(escola_id, ano))
    return ResumoCompleto(
        turmas=ResumoExecucao.de_entidade(ex_t), vinculos=ResumoExecucao.de_entidade(ex_v)
    )


@roteador.get("/sincronizacoes", response_model=list[ResumoExecucao])
def listar_execucoes(sessao: Session = Depends(obter_sessao)) -> list[ResumoExecucao]:
    repo = ExecucaoRepo(sessao)
    return [ResumoExecucao.de_entidade(e) for e in repo.listar()]


@roteador.delete("/sincronizacoes", response_model=dict)
def limpar_execucoes(sessao: Session = Depends(obter_sessao)) -> dict:
    repo = ExecucaoRepo(sessao)
    n = repo.limpar()
    sessao.commit()
    return {"removidas": n}


@roteador.get("/sincronizacoes/{execucao_id}", response_model=DetalheExecucao)
def obter_execucao(execucao_id: int, sessao: Session = Depends(obter_sessao)) -> DetalheExecucao:
    repo = ExecucaoRepo(sessao)
    exec_ = repo.obter(execucao_id)
    if exec_ is None:
        raise HTTPException(status_code=404, detail="execucao nao encontrada")
    base = ResumoExecucao.de_entidade(exec_).model_dump()
    base["falhas_detalhadas"] = [DetalheFalha.de_entidade(f) for f in exec_.falhas_detalhadas]
    return DetalheExecucao(**base)


class EstadoSaude(BaseModel):
    banco: str
    moodle: dict[str, Any] | None = None
    moodle_erro: str | None = None


@roteador.get("/saude", response_model=EstadoSaude)
def saude(sessao: Session = Depends(obter_sessao)) -> EstadoSaude:
    from sqlalchemy import text

    from app.composicao import construir_moodle

    try:
        sessao.execute(text("SELECT 1"))
        banco_status = "ok"
    except Exception as exc:
        banco_status = f"erro: {exc}"
    try:
        moodle = construir_moodle()
        info = moodle.site_info()
        return EstadoSaude(banco=banco_status, moodle=info)
    except Exception as exc:
        return EstadoSaude(banco=banco_status, moodle_erro=str(exc))
