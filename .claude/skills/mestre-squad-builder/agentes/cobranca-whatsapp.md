# Funcionário Autônomo: Cobrança via WhatsApp Business

> Primeiro agente do squad da locadora. Construído sobre a skill `mestre-squad-builder`.
> Objetivo: cobrar locatários automaticamente pelo WhatsApp oficial, parando sozinho quando o cliente paga, minimizando o contato manual do dono.

---

## 1. Decisões já tomadas com o dono

| Decisão | Escolha |
|---|---|
| Canal de envio | WhatsApp Business **Platform oficial (Cloud API)** em **número separado** dedicado à cobrança |
| Saber se o cliente pagou | **Webhook automático do Infinity Pay** (a InfinitePay avisa o sistema no instante do pagamento) |
| Bloqueio de veículo | **Fora de escopo nesta fase** — dono ainda não usa bloqueio |
| Filosofia | Minimizar contato manual do locador com o locatário |

---

## 2. Contrato do Agente (papel)

- **Responsabilidade:** enviar a régua de cobrança pelo WhatsApp oficial e parar quando o pagamento for confirmado.
- **Input:** lista de contratos/parcelas com `cliente`, `telefone`, `valor`, `data_vencimento`, `link_pagamento_infinitepay`, `status`.
- **Output:** mensagens enviadas + registro de cada tentativa (log auditável) + sinalização de escalada ao dono quando necessário.
- **Ferramentas:** WhatsApp Cloud API (envio de template), API Infinity Pay (gerar link), fila de agendamento (BullMQ/cron), banco de dados (status das cobranças).
- **NÃO deve:** enviar cobrança de parcela já paga; enviar fora do horário comercial; tomar decisão de risco (escalada/bloqueio/negociação) sem o dono.

---

## 3. Gatilho · Regra · Ação

- **Gatilho:** rotina diária (1x ao dia, ex. 09:00 horário comercial) varre as parcelas em aberto.
- **Regra:** compara a data de hoje com o vencimento e escolhe a mensagem da régua.
- **Ação:** envia o template correto pelo WhatsApp com o link de pagamento. Se pago, não faz nada.

---

## 4. Régua de Cobrança

| Momento | Tom | Conteúdo |
|---|---|---|
| **Dia 0 (vencimento)** | Lembrete amigável | "Oi {nome}! Hoje vence o aluguel do {veiculo} ({valor}). É só pagar pelo link 👇" + link |
| **+1 dia** | Lembrete leve | "Oi {nome}, notei que o pagamento ainda não caiu. Tudo certo? Link aqui 👇" |
| **+3 dias** | Firme e educado | "{nome}, seu aluguel está em atraso. Pra evitar transtornos, regularize por aqui 👇" |
| **+5 dias** | Sério | "Importante: aluguel em atraso há 5 dias. Pague ou fale comigo pra negociar 👇" |
| **+7 dias** | Escalada | **Avisa o DONO primeiro.** Só envia aviso final ao cliente após liberação do dono. |

**Regras da régua:**
- Para de enviar **imediatamente** quando o webhook do Infinity Pay confirma o pagamento.
- Envia **uma** mensagem por etapa (não repete a mesma etapa no mesmo dia).
- Só envia em horário comercial (ex. 08:00–20:00) para não irritar nem ferir boas práticas do WhatsApp.
- Cliente que **responde** (contesta, reclama, pede negociação) → pausa a régua e escala ao dono.

---

## 5. O que faz sozinho × O que pede aprovação

- ✅ **Autônomo:** etapas Dia 0, +1, +3, +5; anexar link; parar ao pagar; registrar log.
- 🟡 **Pede aprovação do dono:** etapa +7 (escalada), qualquer resposta do cliente, pedidos de desconto/negociação, bloqueio futuro de veículo.

---

## 6. Fluxo Técnico (linha de montagem)

```
[Cron diário 09:00]
      │
      ▼
Varre parcelas em aberto ──► para cada parcela:
      │
      ├─ paga? ──► não faz nada
      │
      └─ em aberto ──► calcula dias vs vencimento
                          │
                          ├─ etapa 0/+1/+3/+5 ─► envia template WhatsApp + link
                          │
                          └─ etapa +7 ─► notifica DONO e aguarda OK

[Webhook Infinity Pay: "pagou"]
      │
      ▼
Marca parcela como paga ──► cancela próximas cobranças dessa parcela
                          └─► (opcional) envia "Recebido! Obrigado 🙏"
```

---

## 7. Integrações e o que precisa ser provisionado

### WhatsApp Business Platform (Cloud API — Meta)
- Conta no **Meta Business Manager** + número de telefone **novo/dedicado** verificado.
- **Templates de mensagem** aprovados pela Meta (categoria *Utility*) — um para cada etapa da régua.
- Token de acesso e Phone Number ID.
- Custo aproximado: ~R$ 0,08–0,15 por conversa de utilidade.

### Infinity Pay (InfinitePay Checkout API)
- Endpoint para gerar link: `POST https://api.checkout.infinitepay.io/links`
- Parâmetros relevantes: `handle`, `redirect_url`, **`webhook_url`** (endereço do nosso sistema que recebe o aviso de pagamento), `order_nsu`, `items`.
- O `webhook_url` é o que avisa o agente que o cliente pagou → gatilho para parar a cobrança.
- Sem mensalidade, sem contrato.

### Infra mínima do agente
- Um serviço com **agendador** (cron/BullMQ) rodando 1x/dia.
- Um **endpoint público** para receber o webhook do Infinity Pay.
- Banco de dados com a tabela de cobranças e seu status/histórico.

---

## 8. Guardas e Validação (regra de ouro do squad)

- **Idempotência:** se o cron rodar duas vezes no mesmo dia, não envia a mesma cobrança duas vezes.
- **Validação de pagamento:** confiar só no webhook oficial do Infinity Pay (assinado/verificado), nunca em suposição.
- **Anti-spam:** respeitar horário comercial e o limite de uma mensagem por etapa.
- **Auditoria:** registrar cada envio (quem, quando, qual etapa, status de entrega do WhatsApp).
- **LGPD:** telefone e dados do cliente usados só para a finalidade de cobrança, com consentimento no contrato de locação.
- **Escalada humana:** qualquer ambiguidade (resposta do cliente, atraso longo) vai para o dono decidir.

---

## 9. Checklist de Lançamento

- [ ] Número dedicado verificado no Meta Business Manager
- [ ] 5 templates de mensagem (Dia 0, +1, +3, +5, +7) submetidos e aprovados pela Meta
- [ ] Conta Infinity Pay com geração de link via API testada
- [ ] `webhook_url` recebendo e confirmando pagamentos corretamente
- [ ] Régua testada com um contrato fake do início ao fim (cobrou → pagou → parou)
- [ ] Horário comercial e anti-duplicidade validados
- [ ] Canal de escalada ao dono funcionando (ex. mensagem no WhatsApp pessoal do dono)
- [ ] Log de auditoria gravando todos os envios

---

## 10. Próximas evoluções (fora do MVP deste agente)

- Confirmação de pagamento com **mensagem de agradecimento** automática.
- **Negociação assistida** (parcelamento) com aprovação do dono.
- Integração com o futuro agente de **Rastreador/Bloqueio** para atraso prolongado.
- Relatório semanal de inadimplência para o agente **Financeiro**.
