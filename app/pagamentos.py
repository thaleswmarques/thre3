#!/usr/bin/env python3
"""
Camada de pagamento — App R3nt
==============================

Gera a cobrança (link de Pix/checkout) num provedor de pagamento. Igual ao
canal de WhatsApp, é PLUGÁVEL: hoje usamos um provedor Fake (offline), e quando
a credencial da InfinitePay chegar, troca-se o provedor sem mexer no resto.

Decisão (ver DECISOES.md):
  - Provedor gera o Pix + avisa o pagamento por WEBHOOK.
  - O ENVIO da mensagem sai do nosso WhatsApp (não do provedor).
"""

import json
import os
import urllib.request


class Pagamentos:
    """Interface: todo provedor sabe criar uma cobrança e devolver o link de pagamento."""

    def criar_cobranca(self, cobranca: dict) -> str:
        raise NotImplementedError


class PagamentosFake(Pagamentos):
    """Provedor de teste: devolve um link fictício, sem chamar ninguém."""

    def criar_cobranca(self, cobranca: dict) -> str:
        return f"https://pague.exemplo.r3nt/{cobranca['id']}"


class PagamentosInfinitePay(Pagamentos):
    """
    Provedor real (InfinitePay) — esqueleto pronto pra ativar.

    Precisa de duas variáveis de ambiente (configurar como secret, nunca no código):
      INFINITEPAY_HANDLE        -> seu @handle na InfinitePay
      INFINITEPAY_WEBHOOK_URL   -> a URL pública do nosso webhook (app/webhook.py)

    ⚠️ Os campos exatos do payload devem ser conferidos na doc oficial
       (infinitepay.io/desenvolvedores) antes de ir pra produção.
    """

    URL = "https://api.checkout.infinitepay.io/links"

    def __init__(self):
        self.handle = os.environ["INFINITEPAY_HANDLE"]
        self.webhook_url = os.environ.get("INFINITEPAY_WEBHOOK_URL", "")
        self.redirect_url = os.environ.get("INFINITEPAY_REDIRECT_URL", "")

    def criar_cobranca(self, cobranca: dict) -> str:
        centavos = int(round(float(cobranca["valor"]) * 100))
        payload = {
            "handle": self.handle,
            "redirect_url": self.redirect_url,
            "webhook_url": self.webhook_url,
            "order_nsu": str(cobranca["id"]),  # nosso id volta no webhook -> dá baixa
            "items": [
                {"name": cobranca["referente"], "price": centavos, "quantity": 1}
            ],
        }
        req = urllib.request.Request(
            self.URL,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=20) as resp:
            dados = json.loads(resp.read().decode("utf-8"))
        # A doc retorna a URL do checkout; aceitamos algumas chaves comuns.
        return dados.get("url") or dados.get("link") or dados.get("checkout_url", "")


def provedor_padrao() -> Pagamentos:
    """Escolhe o provedor: InfinitePay se houver credencial, senão o Fake."""
    if os.getenv("INFINITEPAY_HANDLE"):
        return PagamentosInfinitePay()
    return PagamentosFake()
