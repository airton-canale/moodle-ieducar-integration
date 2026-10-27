"""Persistencia propria da integracao: nao e copia de dados academicos.
Guarda apenas correlacao externa + bitacula de execucao e falhas."""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class StatusExecucao(str, Enum):
    EM_ANDAMENTO = "em_andamento"
    CONCLUIDA = "concluida"
    ABORTADA = "abortada"


class MapeamentoExterno(Base):
    __tablename__ = "mapeamento_externo"
    __table_args__ = (UniqueConstraint("tipo", "id_ieducar", name="uq_mapeamento_tipo_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    tipo: Mapped[str] = mapped_column(String(32), index=True)
    id_ieducar: Mapped[int] = mapped_column(Integer, index=True)
    id_moodle: Mapped[int] = mapped_column(Integer)
    identificador: Mapped[str] = mapped_column(String(255), index=True)
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class ExecucaoSync(Base):
    __tablename__ = "execucao_sync"

    id: Mapped[int] = mapped_column(primary_key=True)
    fluxo: Mapped[str] = mapped_column(String(32))
    escola_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ano: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(32))
    iniciada_em: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    finalizada_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    processados: Mapped[int] = mapped_column(Integer, default=0)
    criados: Mapped[int] = mapped_column(Integer, default=0)
    reaproveitados: Mapped[int] = mapped_column(Integer, default=0)
    falhas: Mapped[int] = mapped_column(Integer, default=0)
    mensagem: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    falhas_detalhadas: Mapped[list[FalhaSync]] = relationship(
        back_populates="execucao", cascade="all, delete-orphan"
    )


class FalhaSync(Base):
    __tablename__ = "falha_sync"

    id: Mapped[int] = mapped_column(primary_key=True)
    execucao_id: Mapped[int] = mapped_column(ForeignKey("execucao_sync.id"), index=True)
    tipo: Mapped[str] = mapped_column(String(32))
    id_ieducar: Mapped[int | None] = mapped_column(Integer, nullable=True)
    descricao: Mapped[str] = mapped_column(String(1000))

    execucao: Mapped[ExecucaoSync] = relationship(back_populates="falhas_detalhadas")
