"""Cliente HTTP sincrono com retry exponencial. 4xx nunca retenta (bug
do nosso lado ou da fonte); 5xx e timeout retentam com backoff."""
from __future__ import annotations

import time
from typing import Any

import httpx

from app.infraestrutura.erros import ErroPermanente, ErroTemporario


class ClienteHttp:
    def __init__(self, base_url: str, timeout_seg: float = 15.0, tentativas: int = 3) -> None:
        self._cliente = httpx.Client(base_url=base_url, timeout=timeout_seg)
        self._tentativas = tentativas

    def fechar(self) -> None:
        self._cliente.close()

    def get(self, caminho: str, params: dict[str, Any] | None = None) -> httpx.Response:
        return self._executar("GET", caminho, params=params)

    def post(
        self,
        caminho: str,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
    ) -> httpx.Response:
        return self._executar("POST", caminho, params=params, data=data)

    def _executar(
        self,
        metodo: str,
        caminho: str,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
    ) -> httpx.Response:
        ultima_excecao: Exception | None = None
        for tentativa in range(1, self._tentativas + 1):
            try:
                resposta = self._cliente.request(metodo, caminho, params=params, data=data)
            except (httpx.ConnectError, httpx.ReadTimeout, httpx.RemoteProtocolError) as exc:
                ultima_excecao = exc
                self._esperar(tentativa)
                continue
            if 500 <= resposta.status_code < 600:
                ultima_excecao = ErroTemporario(f"{resposta.status_code} em {caminho}")
                self._esperar(tentativa)
                continue
            if 400 <= resposta.status_code < 500:
                raise ErroPermanente(f"{resposta.status_code} em {caminho}: {resposta.text[:400]}")
            return resposta
        raise ErroTemporario(f"Falha apos {self._tentativas} tentativas em {caminho}: {ultima_excecao}")

    @staticmethod
    def _esperar(tentativa: int) -> None:
        time.sleep(min(2 ** (tentativa - 1), 8))
