from app.dominios.pessoa.modelos import Pessoa
from app.dominios.vinculo.modelos import Papel, Situacao
from app.infraestrutura.ieducar.tradutor import (
    traduzir_enturmacao,
    traduzir_pessoa,
    traduzir_turma,
)


def test_turma_campos_novos() -> None:
    t = traduzir_turma({"cod_turma": 10, "nm_turma": "1A", "ano": 2025}, ano_padrao=2024)
    assert t and t.id_ieducar == 10 and t.nome == "1A" and t.ano == 2025


def test_turma_campos_legados() -> None:
    t = traduzir_turma({"turma_id": 11, "nome": "2B"}, ano_padrao=2025)
    assert t and t.id_ieducar == 11 and t.ano == 2025


def test_turma_descarta_sem_id() -> None:
    assert traduzir_turma({"nm_turma": "X"}, ano_padrao=2025) is None


def test_pessoa_campos_variados() -> None:
    p = traduzir_pessoa({"cod_aluno": 1, "nome": "Ana Lima", "email": "a@b.com"})
    assert p and p.id_ieducar == 1 and p.email == "a@b.com"


def test_vinculo_inativo_detectado() -> None:
    p = Pessoa(1, "X")
    v = traduzir_enturmacao({"turma_id": 100, "ativo": 0}, p)
    assert v and v.situacao is Situacao.INATIVO


def test_vinculo_papel_professor() -> None:
    p = Pessoa(1, "X")
    v = traduzir_enturmacao({"turma_id": 100, "funcao": "docente"}, p)
    assert v and v.papel is Papel.PROFESSOR


def test_vinculo_descarta_sem_turma() -> None:
    p = Pessoa(1, "X")
    assert traduzir_enturmacao({}, p) is None
