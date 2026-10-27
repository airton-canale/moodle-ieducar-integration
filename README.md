# Integração i-Educar → Moodle

Monólito modular em Python (FastAPI + SQLAlchemy) que sincroniza, de forma síncrona
e idempotente, **pessoas**, **turmas** e **vínculos** do i-Educar para o Moodle.

Projeto da Entrega 1 — Projeto e Arquitetura de Software (PUCRS).

## Arquitetura

```
app/
├── main.py              FastAPI entrypoint + lifespan (schema + agendador)
├── composicao.py        Composition root (http/fake clients)
├── config.py            Pydantic Settings (lê .env)
├── database.py          Engine + SessionLocal + Base
├── agendador.py         APScheduler (sync periódico)
├── dominios/
│   ├── pessoa/          modelos, serviços, portas
│   ├── turma/           modelos, serviços, portas
│   ├── vinculo/         modelos, serviços, portas
│   └── sincronizacao/   api (router), serviços (orquestração), entidades, repositórios
└── infraestrutura/
    ├── http.py          Cliente HTTP com retry/backoff
    ├── ieducar/         cliente http + fake + tradutor payloads
    └── moodle/          cliente http + fake
```

**Decisões arquiteturais:**
- Monólito modular com fronteiras explícitas (portas por domínio) para permitir
  substituir clientes externos sem tocar nas regras.
- Sincronização síncrona com persistência em Postgres (`MapeamentoExterno`,
  `ExecucaoSync`, `FalhaSync`) para idempotência e auditoria.
- Correlação entre sistemas via `idnumber` prefixado (`ieducar-turma-{id}`,
  `ieducar-pessoa-{id}`) — chave natural, sem acoplar IDs do Moodle no i-Educar.

## Requisitos

- Docker + Docker Compose v2.20+ (suporte a `include:`)
- Portas livres no host: `80` (iEducar), `8081` (Moodle), `8000` (integração), `5432` e `5433` (Postgres), `6379` (Redis)

## Subir ambiente completo

Compose unificado via `include:` traz iEducar, Moodle e integração em um único stack.

```bash
cp .env.example .env
docker compose up -d --build
```

Serviços expostos:

| Serviço     | URL                     |
|-------------|-------------------------|
| i-Educar    | http://localhost        |
| Moodle      | http://localhost:8081   |
| **Integração — Painel** | **http://localhost:8000** |
| Integração — Swagger    | http://localhost:8000/docs |
| Integração — ReDoc      | http://localhost:8000/redoc |

## Painel web

Abrindo `http://localhost:8000` tem uma UI mínima com:

- Status de saúde (banco + Moodle) atualizado a cada 10s
- Botões para disparar **sync completa / só turmas / só vínculos** com inputs de `escola_id` e `ano`
- Tabela de execuções (auto-refresh 5s) — clique numa linha vê o detalhe JSON com falhas

Para operação por API crua, `/docs` (Swagger) permite executar qualquer endpoint
diretamente do navegador.

## Observabilidade

**Logs da aplicação** (stdout estruturado via `logging`):

```bash
docker compose logs -f integracao
```

**Tráfego HTTP de saída** (chamadas para i-Educar e Moodle) via
[HTTP Toolkit](https://httptoolkit.com):

1. Abrir HTTP Toolkit → *Intercept* → *Fresh Terminal* (anota `HTTPS_PROXY` e `SSL_CERT_FILE`)
2. Rodar a integração fora do compose, no mesmo terminal:
   ```bash
   source .env && uvicorn app.main:app --port 8000
   ```
3. Todas as requisições de `httpx` (para iEducar/Moodle) aparecem na timeline do Toolkit.

Alternativa dentro do compose: passar `HTTPS_PROXY=http://host.docker.internal:8000`
e o CA do Toolkit via volume para `/etc/ssl/certs/` no serviço `integracao`.

## Gerar credenciais

**i-Educar** — abrir `http://localhost`, logar como admin e inserir no Postgres do
container `ieducar-postgres`:

```sql
INSERT INTO legacy.apis (name) VALUES ('integracao-moodle');
INSERT INTO legacy.apis_access_key (api_id, access_key)
  VALUES ((SELECT id FROM legacy.apis WHERE name='integracao-moodle'), 'TROQUE_AQUI');
```

Colar `TROQUE_AQUI` em `.env` como `IEDUCAR_ACCESS_KEY`.

**Moodle** — logar como `user` / `bitnami1`, criar um web service external, gerar
token e colar em `.env` como `MOODLE_TOKEN`. Papéis padrão: `5=student`,
`3=editingteacher`.

Reiniciar após editar `.env`:

```bash
docker compose restart integracao
```

## Uso

```bash
# saúde (banco + moodle)
curl http://localhost:8000/saude

# sync completo (turmas + vinculos)
curl -X POST "http://localhost:8000/sincronizacoes/completa?escola_id=1&ano=2025"

# só turmas / só vinculos
curl -X POST "http://localhost:8000/sincronizacoes/turmas?escola_id=1&ano=2025"
curl -X POST "http://localhost:8000/sincronizacoes/vinculos?escola_id=1&ano=2025"

# histórico
curl http://localhost:8000/sincronizacoes
curl http://localhost:8000/sincronizacoes/1
```

Agendador periódico roda sincronização completa a cada
`AGENDADOR_INTERVALO_MIN` minutos (default 15). Desative com
`AGENDADOR_HABILITADO=false`.

## Demonstração

1. No i-Educar: cadastrar escola, turma e matrículas (aluno + professor).
2. `POST /sincronizacoes/completa?escola_id=<id>&ano=2025`
3. Resposta traz `ResumoCompleto` com `criados`, `reaproveitados`, `falhas`.
4. No Moodle: curso aparece em *Site home*, com inscrições esperadas.
5. Rodar o mesmo POST de novo: `criados=0`, tudo em `reaproveitados` — prova
   idempotência (dedup via `MapeamentoExterno` + `idnumber`).

## Desenvolvimento sem a stack

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e '.[dev]'
pytest
IEDUCAR_CLIENTE=fake MOODLE_CLIENTE=fake uvicorn app.main:app --reload --port 8000
```

Modo `fake` usa clientes em memória com dados seed — não precisa iEducar/Moodle.

## Testes

```bash
pytest                # tudo
pytest tests/test_sincronizacao.py -k idempotencia
```

Cobertura: unitários de domínio (pessoa, tradutor), orquestração E2E com fakes
(idempotência, inativação, papéis, falhas), e endpoints HTTP via TestClient.

## Relatório e diagramas

- Diagramas Mermaid navegáveis no GitHub: `docs/arquitetura.md`
- Relatório LaTeX (fontes + PDF): `docs/relatorio/relatorio.tex`
- Compilar PDF local: `make relatorio` (requer `latexmk` + `texlive`)
- Alternativa sem instalar: subir `relatorio.tex` no [Overleaf](https://www.overleaf.com)

## Variáveis de ambiente

Ver `.env.example` — todas documentadas inline.

## Limitações conhecidas

- `FalhaSync` é persistida mas não há reprocessamento automático.
- Schema é criado via `Base.metadata.create_all` no boot (sem Alembic).
- API da integração não exige autenticação — assume rede interna confiável.
- Agendador single-instance (sem lock distribuído).
