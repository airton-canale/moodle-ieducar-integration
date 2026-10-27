"""Agendador sincrono. Timer no mesmo processo, sem brokers nem filas.
max_instances=1 + coalesce=True evita rodadas sobrepostas se uma
execucao demorar mais que o intervalo."""
from __future__ import annotations

import logging

from apscheduler.schedulers.background import BackgroundScheduler

from app.composicao import construir_servico_sync
from app.config import configuracao
from app.database import Sessao
from app.dominios.sincronizacao.servicos import ParametrosFluxo

log = logging.getLogger(__name__)


def _executar_tick() -> None:
    sessao = Sessao()
    try:
        parametros = ParametrosFluxo(
            escola_id=configuracao.escola_id_padrao,
            ano=configuracao.ano_padrao,
            prefixo_turma=configuracao.prefixo_idnumber_turma,
            prefixo_pessoa=configuracao.prefixo_idnumber_pessoa,
            dominio_email=configuracao.dominio_email_sintetico,
            role_aluno=configuracao.moodle_role_aluno,
            role_professor=configuracao.moodle_role_professor,
        )
        servico = construir_servico_sync(sessao)
        servico.sincronizar_completa(parametros)
    except Exception:
        log.exception("tick do agendador falhou")
    finally:
        sessao.close()


def iniciar_agendador() -> BackgroundScheduler | None:
    if not configuracao.agendador_habilitado:
        return None
    sched = BackgroundScheduler(timezone="America/Sao_Paulo")
    sched.add_job(
        _executar_tick,
        trigger="interval",
        minutes=configuracao.agendador_intervalo_min,
        max_instances=1,
        coalesce=True,
        id="sync-completa",
    )
    sched.start()
    return sched
