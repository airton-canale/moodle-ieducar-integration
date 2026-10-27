# Arquitetura

## Visão de componentes

```mermaid
flowchart LR
    subgraph iEducar[i-Educar]
        IE_API[API Legada<br/>CheckToken]
        IE_DB[(Postgres<br/>iEducar)]
        IE_API --> IE_DB
    end

    subgraph Integracao[Integração Monólito Modular]
        API[FastAPI Router<br/>/sincronizacoes/*]
        SVC[Serviço de Sincronização<br/>orquestra turmas + vinculos]
        PESSOA[Dominio Pessoa<br/>portas + regras]
        TURMA[Dominio Turma]
        VINCULO[Dominio Vinculo]
        TRAD[Tradutor iEducar<br/>normaliza payloads]
        CLI_IE[Cliente iEducar<br/>http com retry]
        CLI_MD[Cliente Moodle<br/>http com retry]
        REPO[(Postgres Integracao<br/>MapeamentoExterno,<br/>ExecucaoSync, FalhaSync)]
        SCHED[APScheduler<br/>sync periódico]

        API --> SVC
        SCHED --> SVC
        SVC --> PESSOA
        SVC --> TURMA
        SVC --> VINCULO
        SVC --> REPO
        PESSOA --> CLI_IE
        TURMA --> CLI_IE
        VINCULO --> CLI_IE
        CLI_IE --> TRAD
        PESSOA --> CLI_MD
        TURMA --> CLI_MD
        VINCULO --> CLI_MD
    end

    subgraph Moodle
        MD_API[Moodle Web Services<br/>REST + token]
        MD_DB[(MariaDB)]
        MD_API --> MD_DB
    end

    CLI_IE -->|GET /modules/Api/...| IE_API
    CLI_MD -->|POST webservice/rest| MD_API
```

## Fluxo de sincronização completa

```mermaid
sequenceDiagram
    autonumber
    participant C as Cliente / Scheduler
    participant API as FastAPI
    participant SVC as Serviço Sync
    participant IE as Cliente iEducar
    participant MD as Cliente Moodle
    participant DB as Repo Integração

    C->>API: POST /sincronizacoes/completa?escola_id&ano
    API->>SVC: sincronizar_completa(parametros)
    SVC->>DB: cria ExecucaoSync(fluxo=turmas, status=rodando)

    loop para cada turma do iEducar
        SVC->>IE: listar_turmas(escola_id, ano)
        IE-->>SVC: payload normalizado
        SVC->>DB: busca MapeamentoExterno por idnumber
        alt não existe
            SVC->>MD: criar_curso(idnumber, nome)
            MD-->>SVC: course_id
            SVC->>DB: grava MapeamentoExterno
        else existe
            SVC->>SVC: reaproveitado++
        end
    end

    SVC->>DB: finaliza ExecucaoSync(turmas, ok)
    SVC->>DB: cria ExecucaoSync(fluxo=vinculos)

    loop para cada vinculo (matricula/professor)
        SVC->>IE: listar_vinculos(escola_id, ano)
        SVC->>MD: upsert_usuario(idnumber, email, nome)
        SVC->>MD: inscrever(course_id, user_id, role)
        Note over MD: idempotente via idnumber
    end

    SVC->>DB: finaliza ExecucaoSync(vinculos, ok)
    SVC-->>API: (ex_turmas, ex_vinculos)
    API-->>C: ResumoCompleto JSON
```

## Deployment

```mermaid
flowchart TB
    subgraph Host[Docker Host]
        subgraph net[Rede do Compose Unificado]
            ieducar[ieducar-nginx<br/>ieducar-fpm<br/>ieducar-horizon]
            ieducarpg[(ieducar-postgres)]
            ieducarrd[(ieducar-redis)]
            moodle[moodle]
            mariadb[(mariadb)]
            integ[integracao-ieducar-moodle<br/>FastAPI :8000]
            banco[(integracao-banco<br/>Postgres :5433)]
        end
    end

    ieducar --> ieducarpg
    ieducar --> ieducarrd
    moodle --> mariadb
    integ --> banco
    integ --> ieducar
    integ --> moodle
```

## Decisões técnicas

| Decisão | Alternativa | Motivo |
|---|---|---|
| Monólito modular com portas por domínio | Microserviços | Escopo pequeno, deploy único, troca de clientes externos continua barata. |
| Sincronização síncrona com Postgres de controle | Fila (Celery/RabbitMQ) | Enunciado exige síncrono; auditoria completa cabe em 3 tabelas. |
| `idnumber` prefixado como chave de correlação | Guardar ID Moodle em iEducar | iEducar é read-only sob nossa ótica; `idnumber` já é um campo nativo do Moodle. |
| APScheduler in-process | Cron externo / Celery beat | Sem dependências extras; monólito já roda. Limitação assumida: single-instance. |
| SQLAlchemy 2.0 + psycopg3 | Django ORM | FastAPI-first, menos peso; migrações feitas por `create_all` (limitação assumida). |
| Clientes http + fake atrás da mesma porta | Mock em teste apenas | Fake acelera dev local e testes E2E sem precisar subir Moodle. |
| httpx com retry/backoff e classificação de erro | requests simples | Erros transitórios do iEducar/Moodle são comuns; isola falha fatal vs. retriável. |
