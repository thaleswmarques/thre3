#!/usr/bin/env python3
"""
Webhook de pagamento — App R3nt
===============================

Recebe o aviso da InfinitePay de que uma cobrança foi PAGA e dá baixa: marca a
cobrança como `pago` no dados/cobrancas.csv. A partir daí, o motor de
notificações para de cobrar aquele cliente automaticamente.

Como a InfinitePay encontra a cobrança certa: a gente manda o nosso `id` no
campo `order_nsu` ao criar a cobrança (app/pagamentos.py); ela devolve esse
mesmo valor no webhook.

Como rodar:
    # 1) Subir o servidor que escuta o webhook (porta 8000 por padrão):
    python3 app/webhook.py

    # 2) Testar offline, simulando um pagamento sem HTTP:
    python3 app/webhook.py --simular 1     # marca a cobrança de id 1 como paga

Em produção, a porta 8000 fica atrás de uma URL pública (HTTPS) cadastrada como
INFINITEPAY_WEBHOOK_URL. Confirmar o formato exato do payload na doc oficial.
"""

import csv
import json
import os
import sys
from datetime import date
from http.server import BaseHTTPRequestHandler, HTTPServer

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_COBRANCAS = os.path.join(RAIZ, "dados", "cobrancas.csv")


def marcar_pago(cobranca_id: str, data_pagamento: str) -> bool:
    """Marca a cobrança como paga no CSV. Retorna True se encontrou e atualizou."""
    cobranca_id = str(cobranca_id)
    with open(CSV_COBRANCAS, newline="", encoding="utf-8") as f:
        leitor = csv.DictReader(f)
        campos = leitor.fieldnames
        linhas = list(leitor)

    achou = False
    for linha in linhas:
        if linha["id"] == cobranca_id and linha["status"].strip().lower() == "pendente":
            linha["status"] = "pago"
            linha["pago_em"] = data_pagamento
            achou = True

    if achou:
        with open(CSV_COBRANCAS, "w", newline="", encoding="utf-8") as f:
            escritor = csv.DictWriter(f, fieldnames=campos)
            escritor.writeheader()
            escritor.writerows(linhas)
    return achou


def extrair_id_pago(payload: dict):
    """Lê o id da cobrança paga do payload do webhook (campos comuns)."""
    # A InfinitePay devolve o nosso identificador em order_nsu; aceitamos variações.
    return payload.get("order_nsu") or payload.get("orderNsu") or payload.get("id")


class WebhookHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        tamanho = int(self.headers.get("Content-Length", 0))
        corpo = self.rfile.read(tamanho).decode("utf-8") if tamanho else "{}"
        try:
            payload = json.loads(corpo)
        except json.JSONDecodeError:
            self.send_response(400)
            self.end_headers()
            return

        cobranca_id = extrair_id_pago(payload)
        if cobranca_id and marcar_pago(cobranca_id, date.today().isoformat()):
            print(f"✅ Pagamento recebido: cobrança {cobranca_id} marcada como paga.")
            self.send_response(200)
        else:
            print(f"⚠️ Webhook sem cobrança correspondente: {payload}")
            self.send_response(404)
        self.end_headers()

    def log_message(self, *args):
        pass  # silencia o log padrão do http.server


def rodar_servidor(porta: int):
    print(f"Webhook ouvindo em http://0.0.0.0:{porta}  (Ctrl+C para parar)")
    HTTPServer(("0.0.0.0", porta), WebhookHandler).serve_forever()


def main():
    if "--simular" in sys.argv:
        i = sys.argv.index("--simular")
        cobranca_id = sys.argv[i + 1]
        if marcar_pago(cobranca_id, date.today().isoformat()):
            print(f"✅ (simulação) Cobrança {cobranca_id} marcada como paga.")
        else:
            print(f"⚠️ (simulação) Cobrança {cobranca_id} não encontrada ou já paga.")
        return
    porta = int(os.getenv("PORT", "8000"))
    rodar_servidor(porta)


if __name__ == "__main__":
    main()
