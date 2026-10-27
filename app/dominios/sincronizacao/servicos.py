"""Orquestracao do sync. Importa apenas portas, nunca infra. Falha de
UM registro vira linha em falha_sync; falha ao LISTAR a fonte aborta a
execucao, pois seguir cegamente dessincronizaria o espelho."""
from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.dominios.pessoa.portas import DestinoDeUsuarios
from app.dominios.pessoa.servicos import garantir_usuario
from app.dominios.sincronizacao.entidades import ExecucaoSync, StatusExecucao
from app.dominios.sincronizacao.repositorios import ExecucaoRepo, MapeamentoRepo
from app.dominios.turma.portas import DestinoDeCursos, FonteDeTurmas
from app.dominios.turma.servicos import garantir_curso, montar_idnumber as idnumber_turma
from app.dominios.vinculo.modelos import Papel, Situacao
from app.dominios.vinculo.portas import DestinoDeInscricoes, FonteDeVinculos
from app.dominios.vinculo.servicos import role_id_para_papel
from app.infraestrutura.erros import ErroIntegracao


@dataclass(frozen=True, slots=True)
class ParametrosFluxo:
    escola_id: int | None
    ano: int
    prefixo_turma: str
    prefixo_pessoa: str
    dominio_email: str
    role_aluno: int
    role_professor: int


class ServicoSincronizacao:
    def __init__(
        self,
        sessao: Session,
        fonte_turmas: FonteDeTurmas,
        fonte_vinculos: FonteDeVinculos,
        destino_cursos: DestinoDeCursos,
        destino_usuarios: DestinoDeUsuarios,
        destino_inscricoes: DestinoDeInscricoes,
    ) -> None:
        self._s = sessao
        self._ft = fonte_turmas
        self._fv = fonte_vinculos
        self._dc = destino_cursos
        self._du = destino_usuarios
        self._di = destino_inscricoes
        self._map = MapeamentoRepo(sessao)
        self._exec = ExecucaoRepo(sessao)

    # ---- Turmas -> Cursos ----
    def sincronizar_turmas(self, p: ParametrosFluxo) -> ExecucaoSync:
        execucao = self._exec.iniciar("turmas", p.escola_id, p.ano)
        self._s.commit()
        try:
            try:
                turmas = self._ft.listar_turmas(p.escola_id, p.ano)
            except ErroIntegracao as exc:
                self._exec.finalizar(execucao, StatusExecucao.ABORTADA, f"fonte: {exc}")
                self._s.commit()
                return execucao

            cache_cursos = self._map.cache_por_tipo("curso")
            for turma in turmas:
                execucao.processados += 1
                try:
                    tamanho_antes = len(cache_cursos)
                    course_id = garantir_curso(turma, self._dc, p.prefixo_turma, cache_cursos)
                    if len(cache_cursos) > tamanho_antes:
                        execucao.criados += 1
                    else:
                        execucao.reaproveitados += 1
                    self._map.gravar("curso", turma.id_ieducar, course_id, idnumber_turma(turma, p.prefixo_turma))
                except ErroIntegracao as exc:
                    self._exec.registrar_falha(execucao, "turma", turma.id_ieducar, str(exc))
                self._s.commit()
            self._exec.finalizar(execucao, StatusExecucao.CONCLUIDA)
            self._s.commit()
            return execucao
        except Exception as exc:  # ponytail: salvaguarda final
            self._s.rollback()
            self._exec.finalizar(execucao, StatusExecucao.ABORTADA, f"inesperado: {exc}")
            self._s.commit()
            raise

    # ---- Vinculos -> Usuarios + Inscricoes ----
    def sincronizar_vinculos(self, p: ParametrosFluxo) -> ExecucaoSync:
        execucao = self._exec.iniciar("vinculos", p.escola_id, p.ano)
        self._s.commit()
        try:
            try:
                vinculos = self._fv.listar_vinculos(p.escola_id, p.ano)
            except ErroIntegracao as exc:
                self._exec.finalizar(execucao, StatusExecucao.ABORTADA, f"fonte: {exc}")
                self._s.commit()
                return execucao

            cache_cursos = self._map.cache_por_tipo("curso")
            cache_usuarios = self._map.cache_por_tipo("usuario")

            for vinculo in vinculos:
                execucao.processados += 1
                try:
                    idn_turma = f"{p.prefixo_turma}{vinculo.turma_id}"
                    course_id = cache_cursos.get(idn_turma)
                    if course_id is None:
                        course_id = self._dc.buscar_por_idnumber(idn_turma)
                        if course_id is not None:
                            cache_cursos[idn_turma] = course_id
                            self._map.gravar("curso", vinculo.turma_id, course_id, idn_turma)
                    if course_id is None:
                        # Turma ausente: sync de turmas nao rodou ainda.
                        raise ErroIntegracao(f"turma {vinculo.turma_id} nao mapeada no Moodle")

                    tamanho_antes = len(cache_usuarios)
                    user_id = garantir_usuario(
                        vinculo.pessoa, self._du, p.prefixo_pessoa, p.dominio_email, cache_usuarios
                    )
                    if len(cache_usuarios) > tamanho_antes:
                        execucao.criados += 1
                    else:
                        execucao.reaproveitados += 1
                    self._map.gravar(
                        "usuario",
                        vinculo.pessoa.id_ieducar,
                        user_id,
                        f"{p.prefixo_pessoa}{vinculo.pessoa.id_ieducar}",
                    )

                    if vinculo.situacao is Situacao.INATIVO:
                        self._di.desinscrever(user_id, course_id)
                    else:
                        role_id = role_id_para_papel(vinculo.papel, p.role_aluno, p.role_professor)
                        self._di.inscrever(user_id, course_id, role_id)
                except ErroIntegracao as exc:
                    self._exec.registrar_falha(
                        execucao, "vinculo", vinculo.pessoa.id_ieducar, str(exc)
                    )
                self._s.commit()

            self._exec.finalizar(execucao, StatusExecucao.CONCLUIDA)
            self._s.commit()
            return execucao
        except Exception as exc:
            self._s.rollback()
            self._exec.finalizar(execucao, StatusExecucao.ABORTADA, f"inesperado: {exc}")
            self._s.commit()
            raise

    def sincronizar_completa(self, p: ParametrosFluxo) -> tuple[ExecucaoSync, ExecucaoSync]:
        ex_turmas = self.sincronizar_turmas(p)
        ex_vinculos = self.sincronizar_vinculos(p)
        return ex_turmas, ex_vinculos
