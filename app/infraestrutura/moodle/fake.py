"""Moodle em memoria. Honra as mesmas portas (buscar/criar/inscrever)
e permite rodar o pipeline inteiro sem Moodle rodando."""
from __future__ import annotations

from dataclasses import dataclass, field

from app.dominios.pessoa.modelos import Pessoa
from app.dominios.turma.modelos import Turma


@dataclass
class _Curso:
    id: int
    idnumber: str
    fullname: str
    shortname: str


@dataclass
class _Usuario:
    id: int
    idnumber: str
    username: str
    email: str


@dataclass
class _Inscricao:
    user_id: int
    course_id: int
    role_id: int


@dataclass
class MoodleFake:
    cursos: dict[int, _Curso] = field(default_factory=dict)
    usuarios: dict[int, _Usuario] = field(default_factory=dict)
    inscricoes: list[_Inscricao] = field(default_factory=list)
    _prox_curso: int = 1000
    _prox_usuario: int = 2000

    def site_info(self) -> dict[str, object]:
        return {"sitename": "Moodle Fake", "siteurl": "fake://moodle"}

    def buscar_curso_por_idnumber(self, idnumber: str) -> int | None:
        for curso in self.cursos.values():
            if curso.idnumber == idnumber:
                return curso.id
        return None

    def criar_curso(self, turma: Turma, idnumber: str) -> int:
        self._prox_curso += 1
        novo = _Curso(id=self._prox_curso, idnumber=idnumber, fullname=turma.fullname(), shortname=turma.shortname())
        self.cursos[novo.id] = novo
        return novo.id

    def buscar_usuario_por_idnumber(self, idnumber: str) -> int | None:
        for u in self.usuarios.values():
            if u.idnumber == idnumber:
                return u.id
        return None

    def criar_usuario(self, pessoa: Pessoa, idnumber: str, username: str, email: str) -> int:
        self._prox_usuario += 1
        u = _Usuario(id=self._prox_usuario, idnumber=idnumber, username=username, email=email)
        self.usuarios[u.id] = u
        return u.id

    def inscrever(self, user_id: int, course_id: int, role_id: int) -> None:
        # idempotente: ignora duplicata com mesmo papel
        for i in self.inscricoes:
            if i.user_id == user_id and i.course_id == course_id and i.role_id == role_id:
                return
        self.inscricoes.append(_Inscricao(user_id=user_id, course_id=course_id, role_id=role_id))

    def desinscrever(self, user_id: int, course_id: int) -> None:
        self.inscricoes = [i for i in self.inscricoes if not (i.user_id == user_id and i.course_id == course_id)]
