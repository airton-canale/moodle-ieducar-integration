"""Entrypoint FastAPI. lifespan cria tabelas e sobe o agendador."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse

from app.agendador import iniciar_agendador
from app.database import Base, engine
# ruff: noqa: F401 - import que registra entidades no metadata
from app.dominios.sincronizacao import entidades  # noqa: F401
from app.dominios.sincronizacao.api import roteador

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    Base.metadata.create_all(engine)
    sched = iniciar_agendador()
    try:
        yield
    finally:
        if sched is not None:
            sched.shutdown(wait=False)


app = FastAPI(title="Integracao i-Educar -> Moodle", lifespan=lifespan)
app.include_router(roteador)

_INDEX = Path(__file__).parent / "web" / "index.html"


@app.get("/", include_in_schema=False)
def ui() -> FileResponse:
    return FileResponse(_INDEX)
