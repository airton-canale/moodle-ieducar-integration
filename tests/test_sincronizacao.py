from app.dominios.sincronizacao.entidades import StatusExecucao
from app.dominios.turma.modelos import Turma
from app.dominios.vinculo.modelos import Papel, Situacao, Vinculo
from app.dominios.pessoa.modelos import Pessoa


def test_sync_completa_cria_tudo(servico, parametros, moodle_fake, ieducar_fake) -> None:
    ex_t, ex_v = servico.sincronizar_completa(parametros)
    assert ex_t.status == StatusExecucao.CONCLUIDA.value
    assert ex_v.status == StatusExecucao.CONCLUIDA.value
    assert len(moodle_fake.cursos) == len(ieducar_fake.turmas)
    assert len(moodle_fake.usuarios) >= 3  # fakes incluem 4 pessoas, uma inativa ainda cria usuario


def test_segunda_rodada_nao_duplica(servico, parametros, moodle_fake) -> None:
    servico.sincronizar_completa(parametros)
    cursos_apos_primeira = len(moodle_fake.cursos)
    usuarios_apos_primeira = len(moodle_fake.usuarios)
    inscricoes_apos_primeira = len(moodle_fake.inscricoes)

    servico.sincronizar_completa(parametros)

    assert len(moodle_fake.cursos) == cursos_apos_primeira
    assert len(moodle_fake.usuarios) == usuarios_apos_primeira
    assert len(moodle_fake.inscricoes) == inscricoes_apos_primeira


def test_vinculo_inativo_desinscreve(servico, parametros, moodle_fake) -> None:
    servico.sincronizar_completa(parametros)
    # Pessoa 3 esta INATIVO em turma 102 nos seeds; nao deve ter inscricao
    user_id = moodle_fake.buscar_usuario_por_idnumber("ieducar-pessoa-3")
    course_id = moodle_fake.buscar_curso_por_idnumber("ieducar-turma-102")
    inscr = [i for i in moodle_fake.inscricoes if i.user_id == user_id and i.course_id == course_id]
    assert inscr == []


def test_professor_recebe_role_correto(servico, parametros, moodle_fake) -> None:
    servico.sincronizar_completa(parametros)
    user_id = moodle_fake.buscar_usuario_por_idnumber("ieducar-pessoa-9")
    inscr = [i for i in moodle_fake.inscricoes if i.user_id == user_id]
    assert inscr and all(i.role_id == parametros.role_professor for i in inscr)


def test_vinculo_sem_turma_vira_falha(servico, parametros, ieducar_fake) -> None:
    # Vinculo apontando para turma inexistente
    pessoa_orfa = Pessoa(id_ieducar=777, nome="Orfao Teste")
    ieducar_fake.vinculos.append(
        Vinculo(pessoa=pessoa_orfa, turma_id=999, papel=Papel.ALUNO, situacao=Situacao.ATIVO)
    )
    _, ex_v = servico.sincronizar_completa(parametros)
    assert ex_v.falhas >= 1


def test_fonte_offline_aborta_execucao(servico, parametros, ieducar_fake) -> None:
    ieducar_fake.levantar_erro = True
    ex_t = servico.sincronizar_turmas(parametros)
    assert ex_t.status == StatusExecucao.ABORTADA.value


def test_curso_criado_fora_do_cache_e_reaproveitado(servico, parametros, moodle_fake, ieducar_fake) -> None:
    # Alguem cria o curso no Moodle fora da integracao
    turma = ieducar_fake.turmas[0]
    moodle_fake.criar_curso(turma, f"ieducar-turma-{turma.id_ieducar}")
    cursos_antes = len(moodle_fake.cursos)
    servico.sincronizar_turmas(parametros)
    # Nao deve ter criado duplicado
    assert len(moodle_fake.cursos) == cursos_antes
