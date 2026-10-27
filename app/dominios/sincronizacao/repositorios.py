"""Repositorios finos sobre as entidades. Isolam SQLAlchemy do servico."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.dominios.sincronizacao.entidades import (
    ExecucaoSync,
    FalhaSync,
    MapeamentoExterno,
    StatusExecucao,
)


class MapeamentoRepo:
    def __init__(self, sessao: Session) -> None:
        self._s = sessao

    def obter_id_moodle(self, tipo: str, id_ieducar: int) -> int | None:
        q = select(MapeamentoExterno.id_moodle).where(
            MapeamentoExterno.tipo == tipo, MapeamentoExterno.id_ieducar == id_ieducar
        )
        return self._s.execute(q).scalar_one_or_none()

    def gravar(self, tipo: str, id_ieducar: int, id_moodle: int, identificador: str) -> None:
        existente = self._s.execute(
            select(MapeamentoExterno).where(
                MapeamentoExterno.tipo == tipo, MapeamentoExterno.id_ieducar == id_ieducar
            )
        ).scalar_one_or_none()
        if existente is None:
            self._s.add(
                MapeamentoExterno(
                    tipo=tipo, id_ieducar=id_ieducar, id_moodle=id_moodle, identificador=identificador
                )
            )
        else:
            existente.id_moodle = id_moodle
            existente.identificador = identificador
            existente.atualizado_em = datetime.now(timezone.utc)
        self._s.flush()

    def cache_por_tipo(self, tipo: str) -> dict[str, int]:
        """Chave: identificador (idnumber). Valor: id_moodle. Serve como
        cache local para evitar roundtrip ao Moodle a cada registro."""
        q = select(MapeamentoExterno.identificador, MapeamentoExterno.id_moodle).where(
            MapeamentoExterno.tipo == tipo
        )
        return {ident: id_moodle for ident, id_moodle in self._s.execute(q).all()}


class ExecucaoRepo:
    def __init__(self, sessao: Session) -> None:
        self._s = sessao

    def iniciar(self, fluxo: str, escola_id: int | None, ano: int) -> ExecucaoSync:
        exec_ = ExecucaoSync(
            fluxo=fluxo,
            escola_id=escola_id,
            ano=ano,
            status=StatusExecucao.EM_ANDAMENTO.value,
            iniciada_em=datetime.now(timezone.utc),
        )
        self._s.add(exec_)
        self._s.flush()
        return exec_

    def finalizar(self, execucao: ExecucaoSync, status: StatusExecucao, mensagem: str | None = None) -> None:
        execucao.status = status.value
        execucao.finalizada_em = datetime.now(timezone.utc)
        if mensagem:
            execucao.mensagem = mensagem[:1000]
        self._s.flush()

    def registrar_falha(self, execucao: ExecucaoSync, tipo: str, id_ieducar: int | None, descricao: str) -> None:
        self._s.add(
            FalhaSync(
                execucao_id=execucao.id, tipo=tipo, id_ieducar=id_ieducar, descricao=descricao[:1000]
            )
        )
        execucao.falhas += 1
        self._s.flush()

    def listar(self, limite: int = 50) -> list[ExecucaoSync]:
        q = select(ExecucaoSync).order_by(ExecucaoSync.id.desc()).limit(limite)
        return list(self._s.execute(q).scalars().all())

    def obter(self, execucao_id: int) -> ExecucaoSync | None:
        return self._s.get(ExecucaoSync, execucao_id)

    def limpar(self) -> int:
        from sqlalchemy import delete

        self._s.execute(delete(FalhaSync))
        n = self._s.execute(delete(ExecucaoSync)).rowcount or 0
        self._s.flush()
        return n
