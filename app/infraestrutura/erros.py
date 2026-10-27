"""Hierarquia de erros compartilhada. Separar temporario x permanente
dirige o retry: 5xx/timeout retenta, 4xx/validacao nao."""
from __future__ import annotations


class ErroIntegracao(Exception):
    pass


class ErroTemporario(ErroIntegracao):
    pass


class ErroPermanente(ErroIntegracao):
    pass


class ErroIEducar(ErroIntegracao):
    def __init__(self, mensagem: str, temporario: bool = False):
        super().__init__(mensagem)
        self.temporario = temporario


class ErroMoodle(ErroIntegracao):
    def __init__(self, mensagem: str, codigo: str | None = None, temporario: bool = False):
        super().__init__(mensagem)
        self.codigo = codigo
        self.temporario = temporario
