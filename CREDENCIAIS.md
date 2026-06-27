# 🔑 Passo a passo das credenciais — App R3nt

Guia pra conseguir cada chave. Ordem por facilidade: comece pela 1.

> ⚠️ **Nunca cole as chaves no chat nem no código.** Elas entram como *secret*
> do ambiente. O `.gitignore` já protege o arquivo `.env`. Quando tiver as
> chaves, me avise que eu te mostro onde colocar — sem expor.

---

## 1. 🧠 Claude (IA) — a mais rápida

1. Acesse **platform.claude.com** e crie/entre na conta.
2. Vá em **Billing** e adicione um crédito (uns US$ 5 já dão pra muito teste).
3. Vá em **API Keys** → **Create Key** → dê um nome (ex: "app-r3nt").
4. Copie a chave (começa com `sk-ant-...`). **Guarde num lugar seguro** — ela só
   aparece uma vez.

Variável: `ANTHROPIC_API_KEY`

---

## 2. 📱 WhatsApp (API oficial da Meta) — a mais trabalhosa

É a que dá mais passos, mas é gratuita no nosso volume. Caminho:

1. Tenha uma conta no **Meta Business** (business.facebook.com) — a conta
   comercial da R3nt.
2. Vá em **developers.facebook.com** → **Meus Apps** → **Criar app** →
   tipo **"Empresa/Business"**.
3. No app, adicione o produto **WhatsApp**.
4. A Meta te dá um **número de teste** + um **token temporário** + o
   **Phone Number ID** (ID do número). Já dá pra testar com isso.
5. Pra produção: adicionar **seu número** (ele será migrado pra API — não dá
   mais pra usar o app normal nele), verificar o negócio, e criar um
   **template de mensagem** categoria **"utility"** (texto da cobrança) p/ a
   Meta aprovar.
6. Gerar um **token permanente** (via "System User").

Variáveis: `WHATSAPP_TOKEN` e `WHATSAPP_PHONE_ID`

> 💡 Dá pra começar testando com o número e token **temporários** (passo 4)
> antes de mexer no seu número de verdade.

---

## 3. 💳 InfinitePay (pagamento + webhook)

1. Você já tem conta. Anote o seu **@handle**.
2. Pergunte ao **suporte** (checklist no `DECISOES.md`):
   - Tem **webhook** que avisa quando um Pix/cobrança é **pago**?
   - É no **Checkout/Link** ou na **Gestão de Cobranças recorrente**?
   - Me passam a **documentação da API**?
3. ⚠️ O **webhook precisa de uma URL pública (HTTPS)** apontando pro nosso
   `webhook.py` — ou seja, depende de a gente ter **hospedagem** (servidor).
   Então essa credencial só fica 100% útil quando tivermos onde hospedar.

Variáveis: `INFINITEPAY_HANDLE` e `INFINITEPAY_WEBHOOK_URL`

---

## Ordem recomendada

1. **Claude** (testar a IA hoje mesmo).
2. **WhatsApp** com número/token **temporários** (testar envio sem arriscar seu número).
3. **InfinitePay** + **hospedagem** (quando for pra produção de verdade).

Quando tiver qualquer uma, me chama: a gente liga, testa e segue.
