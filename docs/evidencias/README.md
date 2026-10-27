# Evidências da demonstração

Geradas executando a integração com os adaptadores *fake* do i-Educar e do Moodle
(`IEDUCAR_CLIENTE=fake MOODLE_CLIENTE=fake`), sem a stack Docker:

| Arquivo | Conteúdo |
|---|---|
| `01-saude.json` | `GET /saude`: banco e Moodle respondendo |
| `02-sync-primeira.json` | `POST /sincronizacoes/completa?ano=2025`, 1ª rodada: 2 turmas e 4 vínculos criados |
| `03-sync-segunda-idempotente.json` | Mesma chamada, 2ª rodada: `criados=0`, tudo reaproveitado |
| `04-historico.json` | `GET /sincronizacoes`: histórico das 4 execuções |
| `05-painel.png` | Painel web (`/`) com o histórico |

Para reproduzir:

```bash
IEDUCAR_CLIENTE=fake MOODLE_CLIENTE=fake AGENDADOR_HABILITADO=false \
  DATABASE_URL=sqlite:///./demo.sqlite3 uvicorn app.main:app --port 8000
curl -X POST "http://localhost:8000/sincronizacoes/completa?ano=2025"
```
