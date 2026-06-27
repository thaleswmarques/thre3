# 🤖 App R3nt — guia do app

O app de gestão da R3nt, construído como um squad de agentes. Este guia explica
o que cada peça faz, como rodar e como "ligar as chaves" quando for pra produção.

> Visão geral do projeto: `../NORTE.md` · Frota e contas: `../INVENTARIO.md`
> Decisões de tecnologia e fornecedores: `../DECISOES.md`

---

## O que já existe

| Arquivo | O que faz |
|---|---|
| `triagem.py` | 🧠 **Agente de Triagem (IA)** — lê uma mensagem recebida, identifica quem é (cruzando com a base) e encaminha pro setor certo. Usa a Claude. |
| `cobranca.py` | 💰 **Relatório de cobrança** — lê as contas a receber, mostra atrasado/a receber/negociação e gera mensagens. |
| `notificacoes.py` | ⚙️ **Motor de notificações** — o coração: dispara a cobrança no vencimento, +1 e +3 dias (com aviso de bloqueio). |
| `pagamentos.py` | 💳 **Camada de pagamento** — gera o link de Pix (InfinitePay) e manda nosso `id` p/ casar com o webhook. |
| `webhook.py` | 📥 **Webhook de pagamento** — recebe o aviso de "pago" e dá baixa automática. |
| `canais.py` | 📱 **Canais de envio** — manda a mensagem (console p/ teste; WhatsApp Cloud p/ produção). |

Dados (na pasta `../dados/`): `frota.csv`, `contas-a-receber.csv`, `cobrancas.csv`.

---

## Como rodar (offline, sem nenhuma chave)

```bash
# Triagem (modo demo, sem IA):
python3 app/triagem.py "Oi, é o Marcos do Cactus branco, bati o carro ontem"

# Relatório de cobrança:
python3 app/cobranca.py

# Motor de notificações (usa a data de hoje; --data simula outro dia):
python3 app/notificacoes.py --data 2026-06-27

# Simular um pagamento (dá baixa na cobrança de id 1):
python3 app/webhook.py --simular 1
```

Sem credenciais, o app roda em **modo seguro**: a IA fica em demo, o Pix vira um
link fictício e as mensagens só aparecem no terminal (não enviam nada).

---

## O fluxo de cobrança (ponta a ponta)

```
  cobrancas.csv (quem deve, quanto, vencimento)
        │
        ▼
  notificacoes.py  ──pede o link──▶  pagamentos.py  (gera o Pix)
        │
        ▼  monta a mensagem da etapa (D0 / D+1 / D+3-bloqueio)
  canais.py  ──envia──▶  cliente (WhatsApp)
        │
   cliente paga
        ▼
  webhook.py  ◀──avisa "pago"──  InfinitePay
        │
        ▼  marca status=pago no cobrancas.csv
   notificacoes.py para de cobrar esse cliente sozinho
```

---

## As 3 "tomadas" (como ligar cada chave)

O app foi feito com peças **plugáveis**: sem chave, usa a versão de teste; com a
chave, usa a real — **sem mudar o resto do código**. As chaves NUNCA vão no
código; entram como variáveis de ambiente / secret (o `.gitignore` já protege
o `.env`).

### 1. 🧠 IA (Claude) — `triagem.py`
```bash
export ANTHROPIC_API_KEY="sua-chave"
```
Onde pegar: platform.claude.com → API Keys.

### 2. 💳 Pagamento (InfinitePay) — `pagamentos.py` + `webhook.py`
```bash
export INFINITEPAY_HANDLE="seu-handle"
export INFINITEPAY_WEBHOOK_URL="https://seu-dominio/webhook"
```
Com `INFINITEPAY_HANDLE` setado, o app troca o provedor Fake pela InfinitePay
sozinho. Confirmar os campos exatos do webhook na doc oficial (ver checklist no
`../DECISOES.md`).

### 3. 📱 WhatsApp (Cloud API oficial) — `canais.py`
```bash
export WHATSAPP_TOKEN="seu-token"
export WHATSAPP_PHONE_ID="id-do-numero"
```
Com essas duas, o app troca o console pelo WhatsApp sozinho.
⚠️ Cobrança **inicia** a conversa, então a Meta exige um **template "utility"
aprovado** — texto solto só vale dentro da janela de 24h. Ver `../DECISOES.md`.

---

## O que ainda falta pra produção

- [ ] **Agendador**: rodar `notificacoes.py` 1x/dia automático (cron num servidor sempre ligado).
- [ ] **Telefones** dos clientes no `cobrancas.csv` (hoje estão em branco).
- [ ] **Template de cobrança** aprovado no painel da Meta.
- [ ] **Confirmar webhook** da InfinitePay (ou migrar p/ Asaas/OpenPix).
- [ ] **Rastreador**: ver se a Starfence tem API p/ o bloqueio automático (fase 2).

---

## Princípio do projeto

Cada peça é pequena, faz uma coisa e é fácil de entender — porque o Thales está
aprendendo dev do zero e isso aqui também vira conteúdo (vlog) e material (livro).
A regra de ouro: **se é importante, salva no arquivo** (não confia na memória do chat).
