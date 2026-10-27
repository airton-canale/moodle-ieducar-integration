"""Fonte em memoria com dados fixos para rodar o fluxo end-to-end sem
tocar no i-Educar real. Serve tambem como fixture dos testes."""
from __future__ import annotations

from app.dominios.pessoa.modelos import Pessoa
from app.dominios.turma.modelos import Turma
from app.dominios.vinculo.modelos import Papel, Situacao, Vinculo


class IEducarFake:
    def __init__(
        self,
        turmas: list[Turma] | None = None,
        pessoas: list[Pessoa] | None = None,
        vinculos: list[Vinculo] | None = None,
    ) -> None:
        self.turmas = turmas if turmas is not None else _seed_turmas()
        self.pessoas = pessoas if pessoas is not None else _seed_pessoas()
        self.vinculos = vinculos if vinculos is not None else _seed_vinculos(self.pessoas)
        self.levantar_erro = False

    def _talvez_falhar(self) -> None:
        if self.levantar_erro:
            from app.infraestrutura.erros import ErroIEducar

            raise ErroIEducar("fonte offline (fake)", temporario=True)

    def listar_turmas(self, escola_id: int | None, ano: int) -> list[Turma]:
        self._talvez_falhar()
        return [t for t in self.turmas if t.ano == ano and (escola_id is None or t.escola_id == escola_id)]

    def listar_pessoas(self, escola_id: int | None, ano: int) -> list[Pessoa]:
        self._talvez_falhar()
        return list(self.pessoas)

    def listar_vinculos(self, escola_id: int | None, ano: int) -> list[Vinculo]:
        self._talvez_falhar()
        return list(self.vinculos)


def _seed_turmas() -> list[Turma]:
    return [
        Turma(id_ieducar=101, nome="1A", ano=2025, escola_id=1, escola_nome="EM Central", curso_nome="EF", serie_nome="1 ano"),
        Turma(id_ieducar=102, nome="2B", ano=2025, escola_id=1, escola_nome="EM Central", curso_nome="EF", serie_nome="2 ano"),
    ]


def _seed_pessoas() -> list[Pessoa]:
    return [
        Pessoa(id_ieducar=1, nome="Ana Lima", email="ana@example.org", cpf="123.456.789-00"),
        Pessoa(id_ieducar=2, nome="Bruno Souza"),
        Pessoa(id_ieducar=3, nome="Carla", email="carla@example.org"),
        Pessoa(id_ieducar=9, nome="Professora Dora"),
    ]


def _seed_vinculos(pessoas: list[Pessoa]) -> list[Vinculo]:
    por_id = {p.id_ieducar: p for p in pessoas}
    return [
        Vinculo(pessoa=por_id[1], turma_id=101, papel=Papel.ALUNO, situacao=Situacao.ATIVO, matricula_id=11),
        Vinculo(pessoa=por_id[2], turma_id=101, papel=Papel.ALUNO, situacao=Situacao.ATIVO, matricula_id=12),
        Vinculo(pessoa=por_id[3], turma_id=102, papel=Papel.ALUNO, situacao=Situacao.INATIVO, matricula_id=13),
        Vinculo(pessoa=por_id[9], turma_id=101, papel=Papel.PROFESSOR, situacao=Situacao.ATIVO, matricula_id=91),
    ]
