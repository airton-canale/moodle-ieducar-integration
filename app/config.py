"""Configuracao central. Tudo vem de env para que o mesmo binario atenda
local, docker e CI sem recompilar."""
from __future__ import annotations

from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Configuracao(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # i-Educar
    ieducar_base_url: str = "http://host.docker.internal:80"
    ieducar_access_key: str = ""
    ieducar_cliente: Literal["http", "fake"] = "fake"
    ieducar_timeout_seg: float = 15.0

    # Moodle
    moodle_base_url: str = "http://host.docker.internal:8081"
    moodle_token: str = ""
    moodle_cliente: Literal["http", "fake"] = "fake"
    moodle_timeout_seg: float = 15.0
    moodle_role_aluno: int = 5
    moodle_role_professor: int = 3

    # Dominio
    escola_id_padrao: int | None = None
    ano_padrao: int = 2025
    prefixo_idnumber_turma: str = "ieducar-turma-"
    prefixo_idnumber_pessoa: str = "ieducar-pessoa-"
    dominio_email_sintetico: str = "ieducar.local"

    # Banco
    database_url: str = "sqlite:///./integracao.sqlite3"

    # Agendador
    agendador_habilitado: bool = True
    agendador_intervalo_min: int = Field(default=15, ge=1)


configuracao = Configuracao()
