# 🧭 Decisões técnicas — App R3nt

> Registro das escolhas de tecnologia e fornecedores do app, com o porquê.
> Atualizado: 2026-06-27.

## 1. Envio de cobrança no WhatsApp

**Decisão (recomendada): WhatsApp Cloud API oficial (Meta).**

| Opção | Como funciona | Custo | Risco |
|---|---|---|---|
| **Cloud API oficial (Meta)** ⭐ | Número de empresa verificado, migrado p/ a API | Acesso grátis; ~1.000 conversas de serviço/mês grátis; "utility" (lembrete) ~R$ 0,10–0,15 cada → ≈ zero no nosso volume | Baixo (oficial) |
| Evolution API (open source) | Conecta **seu número** via QR (protocolo WhatsApp Web) | Só o servidor (~R$ 30–60/mês) | ⚠️ Não-oficial; risco de **ban** do número em cobrança |

- **Por quê a oficial:** mensagem financeira; um ban dói muito. No nosso volume (poucos clientes) fica praticamente grátis e sai de um número de empresa (pode ter selo → mais confiança que o número pessoal).
- **Pegadinha:** o número registrado é migrado p/ a API — não dá mais p/ usar o app normal nele. Dedicar **um número** só p/ isso.
- Evolution fica como caminho de aprendizado, não p/ cobrança em produção.

## 2. Identificação da quitação (pagamento) + InfinitePay ("Infinity")

**Decisão: desacoplar o envio do recebimento.**

- **Enviar a cobrança** → sai do **nosso número** (item 1). Resolve o problema atual: hoje a InfinitePay envia do número **dela**, e o cliente espera a confirmação do Thales p/ pagar.
- **Detectar a quitação** → via **webhook** do provedor de pagamento (ele avisa o app no instante em que o Pix cai → app marca "quitado" e para os lembretes).

**Provedor de pagamento:**
- A **InfinitePay** entra no escopo (Pix + recorrência + confirmação), mas a **API/webhook p/ dev é limitada**.
- Alternativas mais amigáveis p/ integração: **Asaas** e **OpenPix/Woovi** (webhook de pagamento excelente, Pix barato/zero).
- **A confirmar:** se a InfinitePay expõe webhook de "pago". Se não, migrar essa camada p/ Asaas ou OpenPix.

**Fluxo alvo:** app gera o Pix no provedor → envia do **WhatsApp do Thales** → cliente paga → webhook avisa → app marca quitado → para os lembretes.

## 3. Rastreamento / bloqueio (Starfence)

**Decisão: começar sem integração; automatizar o bloqueio depois.**

- O **lembrete** ("seu carro pode ser bloqueado") **não precisa de integração** — é mensagem agendada.
- O **bloqueio automático** precisa da **API da Starfence** (a confirmar se existe).
- **MVP:** lembrete automático + Thales bloqueia manual no app da Starfence. Automatizar o bloqueio na fase 2.
- **Rastreador próprio + app próprio** (investir os R$ 300/mês): viável, mas é **projeto à parte e maior** (hardware: rastreadores ~R$ 80–200 cada uma vez + chip M2M ~R$ 10–15/mês por carro + servidor 24h). Não deve travar o app de cobrança. Planejar como **fase 2**.

---

## 📋 Perguntas a fazer aos fornecedores

### Para o suporte da **Starfence**
- [ ] Vocês têm **API/webhook** p/ desenvolvedores?
- [ ] Dá p/ **consultar localização** dos veículos via API?
- [ ] Dá p/ enviar **comando de bloqueio/desbloqueio** remoto via API?
- [ ] Tem documentação técnica / área de dev? Tem custo extra pela API?

### Para a **InfinitePay** (ou avaliar Asaas / OpenPix)
- [ ] Vocês têm **webhook** que avisa meu sistema quando um Pix/cobrança é **pago**?
- [ ] Tem **API** p/ gerar cobrança/Pix programaticamente?
- [ ] Consigo usar a InfinitePay só p/ **gerar o Pix + receber a confirmação**, enviando a mensagem pelo **meu** WhatsApp?

---

## Fontes consultadas (27/06/2026)
- WhatsApp Cloud API — custos 2026: blog.umbler.com, socialhub.pro
- Evolution API: hostgator.com.br, horadecodar.com.br
- InfinitePay — gestão de cobrança / recorrência: infinitepay.io
- Pix recorrência / webhooks: openpix.com.br
