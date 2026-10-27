# Prompt para o Claude — Fechar pendências da Entrega 1

Copie o bloco abaixo e cole no Claude Code dentro de `/Users/airtoncanale/Documents/repos/PUCRS/projarc/integration`. Ele descreve o estado atual do projeto, os gaps identificados comparando com o enunciado da Entrega 1 (Projeto e Arquitetura de Software — PUCRS), e os passos ordenados para fechar cada pendência.

---

## Contexto do projeto

Monólito modular em Python (FastAPI + SQLAlchemy) que sincroniza turmas e vínculos do **i-Educar** para o **Moodle**. Todo o ambiente roda em um único `docker-compose` (iEducar + Moodle + integração + Postgres + Redis).

Estrutura relevante já existente:

- `app/` — código-fonte (dominios, infraestrutura, api, web/painel).
- `tests/` — unitários de domínio + E2E com fakes + endpoints HTTP.
- `Dockerfile`, `docker-compose.yml`, `.env.example`, `Makefile`, `pyproject.toml`.
- `README.md` — setup, geração de credenciais, demonstração, limitações.
- `docs/arquitetura.md` — diagramas Mermaid (componentes, sequência, deployment) + tabela de decisões.
- `docs/relatorio/relatorio.tex` — relatório LaTeX (classe `article` genérica, sem template oficial).

## Enunciado da Entrega 1

> Implemente uma integração entre iEducar e Moodle, conforme planejamento da Entrega 1. Aplicação monolítica, Docker Compose obrigatório.
>
> **O que entregar:**
> 1. Repositório com código-fonte, Dockerfiles, Docker Compose e README com instruções.
> 2. Relatório escrito com o template LaTeX oficial, entregue em **PDF e arquivos-fonte**. Deve conter: objetivo, informações sincronizadas, arquitetura e diagrama de fluxo, decisões técnicas, testes, resultados e limitações.
> 3. Demonstração da integração funcionando (dados em origem no iEducar → resultado no Moodle).
>
> **Rubrica:** Funcionamento 4,0 | Arquitetura 2,5 | Consistência e falhas 1,5 | Relatório 1,5 | Demonstração 0,5.

## Gaps identificados

| # | Pendência | Impacto na rubrica |
|---|---|---|
| 1 | **Sem repositório git inicializado.** `git status` retorna *not a git repository*. Enunciado exige "Repositório com código-fonte". | Entrega inválida sem repo. |
| 2 | **PDF do relatório não existe.** Só há `relatorio.tex`. Enunciado exige "entregue em PDF **e** com os arquivos-fonte". | Relatório (1,5). |
| 3 | **Template LaTeX oficial não aplicado.** Atual usa `\documentclass[11pt,a4paper]{article}` genérico. Enunciado linka um template específico do curso ("template em LaTeX"). | Relatório (1,5). |
| 4 | **`.gitignore` não lista artefatos LaTeX (`*.aux`, `*.log`, `*.out`, `*.pdf` gerados fora de `docs/relatorio/`).** Pode poluir o repositório. | Boas práticas. |
| 5 | **README não cita o PDF gerado nem versiona o `.pdf` final** em caminho previsível (`docs/relatorio/relatorio.pdf`). | Avaliação do relatório. |
| 6 | **Falta um `evidencias/` com prints/JSONs da demonstração** (payload da sync, curso no Moodle, idempotência na segunda rodada). Enunciado valoriza "Demonstração" (0,5). | Demonstração (0,5). |
| 7 | **README não menciona explicitamente onde está o PDF e como abrir** depois do `make relatorio`. | Clareza. |

Não são gaps (já cobertos): código fonte, Dockerfile, docker-compose unificado, README com setup, testes rodando, decisões técnicas documentadas, diagramas de arquitetura e fluxo (em `.md` + TikZ no `.tex`), limitações descritas.

## Tarefa para o Claude — passo a passo

Execute as etapas abaixo **em ordem**. Pergunte antes de qualquer ação destrutiva ou que crie commit remoto. Rode `pytest` e `docker compose config` como checks ao final.

### Passo 1 — Inicializar repositório git

1. Rodar `git init` na raiz do projeto.
2. Confirmar/estender `.gitignore` para incluir:
   ```
   __pycache__/
   *.pyc
   .venv/
   .env
   # LaTeX
   *.aux
   *.log
   *.out
   *.toc
   *.fls
   *.fdb_latexmk
   *.synctex.gz
   docs/relatorio/_build/
   ```
   Manter `docs/relatorio/relatorio.pdf` **versionado** (é entregável).
3. Primeiro commit: `chore: initial commit — integração i-Educar → Moodle (Entrega 1)`.
4. **Perguntar ao usuário** antes de criar remote ou dar push. Se o usuário confirmar, criar repositório no GitHub via `gh repo create` (público ou privado conforme preferência dele).

### Passo 2 — Trocar para o template LaTeX oficial do curso

1. Perguntar ao usuário onde está o template oficial (link no Moodle da disciplina, arquivo local, ou fornecer o `.cls`/`.sty`).
2. Se o usuário não tiver o template imediatamente, oferecer dois caminhos:
   - **(a)** Manter `article` com uma declaração explícita no cabeçalho do PDF explicando que o template oficial não foi acessível. Risco: perder nota no critério "Relatório escrito".
   - **(b)** Usar um template padrão PUCRS equivalente (por ex. um `abntex2` básico) até o usuário recuperar o oficial.
3. Após obter o template, migrar o conteúdo atual de `docs/relatorio/relatorio.tex` para a classe/estrutura exigida, preservando todas as seções: **Objetivo, Informações sincronizadas, Arquitetura, Diagrama de fluxo, Decisões técnicas, Testes realizados, Resultados, Limitações, Repositório e execução**.
4. Manter as figuras TikZ (componentes + fluxo) — se o template oficial não suportar `tikz`, exportá-las como PNG via Mermaid CLI e trocar por `\includegraphics`.

### Passo 3 — Gerar o PDF do relatório

1. Verificar/ajustar o `Makefile` para incluir alvo `relatorio`:
   ```make
   relatorio:
   	cd docs/relatorio && latexmk -pdf -interaction=nonstopmode relatorio.tex
   ```
2. Rodar `make relatorio`. Se faltar `latexmk`/`texlive` localmente, oferecer alternativa Docker:
   ```bash
   docker run --rm -v "$PWD/docs/relatorio":/workdir -w /workdir texlive/texlive:latest \
     latexmk -pdf -interaction=nonstopmode relatorio.tex
   ```
3. Confirmar que `docs/relatorio/relatorio.pdf` foi gerado e tem todas as figuras renderizadas (abrir manualmente ou via `qlmanage -p` no macOS para preview).
4. Commitar: `docs: adiciona PDF do relatório da Entrega 1`.

### Passo 4 — Capturar evidências da demonstração

1. Subir a stack: `docker compose up -d --build`.
2. Gerar credenciais (seguir seção "Gerar credenciais" do `README.md`), colar no `.env`, `docker compose restart integracao`.
3. Criar diretório `docs/evidencias/`.
4. Rodar o fluxo e salvar artefatos:
   - **Health check:** `curl http://localhost:8000/saude | tee docs/evidencias/01-saude.json`
   - **Sync completa (1ª rodada):** `curl -X POST "http://localhost:8000/sincronizacoes/completa?escola_id=1&ano=2025" | tee docs/evidencias/02-sync-primeira.json`
   - **Sync completa (2ª rodada — idempotência):** mesma chamada → `docs/evidencias/03-sync-segunda-idempotente.json` (deve mostrar `criados=0`).
   - **Histórico:** `curl http://localhost:8000/sincronizacoes | tee docs/evidencias/04-historico.json`
5. Screenshots (manual ou via `screencapture` no macOS):
   - Painel da integração (`http://localhost:8000`) → `docs/evidencias/05-painel.png`.
   - Curso criado no Moodle (`http://localhost:8081`) → `docs/evidencias/06-moodle-curso.png`.
   - Lista de participantes do curso (aluno + professor com papéis) → `docs/evidencias/07-moodle-participantes.png`.
6. Referenciar essas evidências na seção "Resultados" do `relatorio.tex` com `\includegraphics` e commitar.

### Passo 5 — Atualizar README

1. Adicionar seção "Entrega 1" no topo apontando para:
   - PDF: `docs/relatorio/relatorio.pdf`
   - Fontes: `docs/relatorio/relatorio.tex`
   - Evidências: `docs/evidencias/`
2. Confirmar que a seção "Demonstração" cobre o roteiro exato do Passo 4 (já cobre, revisar).
3. Commit: `docs: aponta entregáveis da Entrega 1 no README`.

### Passo 6 — Checklist final (rodar e reportar)

- [ ] `git log --oneline` mostra ao menos 3 commits coerentes.
- [ ] `pytest` passa sem rede/containers externos.
- [ ] `docker compose config` valida sem erro.
- [ ] `docs/relatorio/relatorio.pdf` existe, abre, tem todas as figuras.
- [ ] `docs/evidencias/` tem os 4 JSONs + 3 PNGs.
- [ ] README cita todos os entregáveis.
- [ ] Rubrica revista item a item (Funcionamento, Arquitetura, Consistência, Relatório, Demonstração) com uma linha dizendo o que no repo cumpre cada ponto.

Reportar ao final: lista de commits criados, caminhos dos entregáveis gerados, e qualquer item que ficou pendente (ex.: template oficial não obtido).

---

**Restrições:**
- Não refatorar código da aplicação. Entrega 1 já funciona; mudanças no `app/` não são pedidas.
- Não criar push para remote sem confirmação explícita do usuário.
- Não apagar o `relatorio.tex` atual antes de garantir que o conteúdo migrou para a nova classe.
- Perguntar antes de instalar `texlive` localmente — oferecer a imagem Docker como alternativa.
