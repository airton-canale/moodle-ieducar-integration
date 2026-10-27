"""Cliente REST do Moodle. Dois cuidados: (1) Moodle devolve HTTP 200
mesmo em erro, com `exception`/`errorcode`/`message`; (2) argumentos
aninhados vao achatados no form (`users[0][username]=...`), nunca JSON."""
from __future__ import annotations

from typing import Any

from app.dominios.pessoa.modelos import Pessoa
from app.dominios.turma.modelos import Turma
from app.infraestrutura.erros import ErroMoodle
from app.infraestrutura.http import ClienteHttp


def _achatar(prefixo: str, valor: Any, destino: dict[str, Any]) -> None:
    """Achata dict/list para o formato que Moodle espera no form."""
    if isinstance(valor, dict):
        for chave, item in valor.items():
            _achatar(f"{prefixo}[{chave}]", item, destino)
    elif isinstance(valor, list):
        for i, item in enumerate(valor):
            _achatar(f"{prefixo}[{i}]", item, destino)
    else:
        destino[prefixo] = valor


def achatar_args(args: dict[str, Any]) -> dict[str, Any]:
    plano: dict[str, Any] = {}
    for chave, valor in args.items():
        _achatar(chave, valor, plano)
    return plano


class ClienteMoodle:
    def __init__(self, http: ClienteHttp, token: str) -> None:
        if not token:
            raise ErroMoodle("MOODLE_TOKEN nao configurado")
        self._http = http
        self._token = token

    def _chamar(self, funcao: str, args: dict[str, Any] | None = None) -> Any:
        params = {"wstoken": self._token, "wsfunction": funcao, "moodlewsrestformat": "json"}
        data = achatar_args(args or {})
        resposta = self._http.post("/webservice/rest/server.php", params=params, data=data)
        try:
            corpo = resposta.json()
        except ValueError as exc:
            raise ErroMoodle(f"Resposta nao-JSON em {funcao}") from exc
        if isinstance(corpo, dict) and corpo.get("exception"):
            raise ErroMoodle(
                f"{funcao}: {corpo.get('message')}",
                codigo=str(corpo.get("errorcode")),
            )
        return corpo

    def site_info(self) -> dict[str, Any]:
        return self._chamar("core_webservice_get_site_info")

    # Cursos
    def buscar_curso_por_idnumber(self, idnumber: str) -> int | None:
        corpo = self._chamar(
            "core_course_get_courses_by_field",
            {"field": "idnumber", "value": idnumber},
        )
        cursos = corpo.get("courses", []) if isinstance(corpo, dict) else []
        return int(cursos[0]["id"]) if cursos else None

    def criar_curso(self, turma: Turma, idnumber: str) -> int:
        corpo = self._chamar(
            "core_course_create_courses",
            {
                "courses": [
                    {
                        "fullname": turma.fullname(),
                        "shortname": turma.shortname(),
                        "categoryid": 1,
                        "idnumber": idnumber,
                    }
                ]
            },
        )
        return int(corpo[0]["id"])

    # Usuarios
    def buscar_usuario_por_idnumber(self, idnumber: str) -> int | None:
        corpo = self._chamar(
            "core_user_get_users_by_field",
            {"field": "idnumber", "values": [idnumber]},
        )
        return int(corpo[0]["id"]) if isinstance(corpo, list) and corpo else None

    def criar_usuario(self, pessoa: Pessoa, idnumber: str, username: str, email: str) -> int:
        firstname, lastname = pessoa.dividir_nome()
        corpo = self._chamar(
            "core_user_create_users",
            {
                "users": [
                    {
                        "username": username,
                        "firstname": firstname,
                        "lastname": lastname,
                        "email": email,
                        "idnumber": idnumber,
                        "auth": "manual",
                        "createpassword": 1,
                    }
                ]
            },
        )
        return int(corpo[0]["id"])

    # Inscricoes
    def inscrever(self, user_id: int, course_id: int, role_id: int) -> None:
        self._chamar(
            "enrol_manual_enrol_users",
            {"enrolments": [{"roleid": role_id, "userid": user_id, "courseid": course_id}]},
        )

    def desinscrever(self, user_id: int, course_id: int) -> None:
        self._chamar(
            "enrol_manual_unenrol_users",
            {"enrolments": [{"userid": user_id, "courseid": course_id}]},
        )
