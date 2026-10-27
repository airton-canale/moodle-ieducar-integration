from app.dominios.pessoa.modelos import Pessoa
from app.dominios.pessoa.servicos import montar_email, montar_idnumber, montar_username


def test_dividir_nome_composto() -> None:
    assert Pessoa(1, "Ana Lima Souza").dividir_nome() == ("Ana", "Lima Souza")


def test_dividir_nome_unico_repete_para_lastname() -> None:
    # Moodle rejeita lastname vazio -> repetir
    assert Pessoa(1, "Madonna").dividir_nome() == ("Madonna", "Madonna")


def test_username_prefere_cpf_quando_presente() -> None:
    assert montar_username(Pessoa(1, "X", cpf="123.456.789-00")) == "12345678900"


def test_username_fallback_sem_cpf() -> None:
    assert montar_username(Pessoa(42, "X")) == "ieducar.pessoa.42"


def test_email_sintetico_quando_sem_email() -> None:
    assert montar_email(Pessoa(7, "X"), "ieducar.local") == "ieducar-pessoa-7@ieducar.local"


def test_email_real_tem_prioridade() -> None:
    assert montar_email(Pessoa(7, "X", email="A@B.com"), "ieducar.local") == "a@b.com"


def test_idnumber_prefixado() -> None:
    assert montar_idnumber(Pessoa(9, "X"), "ieducar-pessoa-") == "ieducar-pessoa-9"
