# thre3 — Jornada R3nt

Base do projeto do Thales: construir o app de gestão da **R3nt** (locadora),
documentando como vlog, rumo a um livro. Aprendendo dev do zero com o Claude Code.

## Mapa do repositório

- **[NORTE.md](NORTE.md)** — a visão (app, vlog, livro).
- **[INVENTARIO.md](INVENTARIO.md)** — frota, contas a receber, financiamentos, IPVA, cálculos.
- **[APP_AGENTES.md](APP_AGENTES.md)** — o squad de agentes do app.
- **[DECISOES.md](DECISOES.md)** — escolhas de tecnologia e fornecedores (WhatsApp, pagamento, rastreador).
- **[atualizacoes.md](atualizacoes.md)** — diário de bordo (novidades por data).
- **[app/](app/)** — o código do app. Comece pelo **[app/README.md](app/README.md)**.
- **[dados/](dados/)** — frota e contas em CSV.
- **CLAUDE.md** — contexto que o Claude lê no início de cada sessão.

## Rodar o app (offline, sem chave)

```bash
python3 app/notificacoes.py --data 2026-06-27   # motor de cobrança
python3 app/cobranca.py                          # relatório de contas
```

Detalhes e como ligar as chaves (IA, pagamento, WhatsApp): **[app/README.md](app/README.md)**.
