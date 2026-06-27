#!/usr/bin/env python3
"""
Motor de Notificações de Cobrança — App R3nt
============================================

Roda uma vez por dia. Para cada cobrança em aberto, calcula há quantos dias ela
venceu e, se hoje for um dos dias da régua, gera e envia a mensagem certa:

  - Dia 0 (vence hoje) ....... aviso amigável de vencimento + Pix
  - Dia +1 (venceu ontem) .... lembrete de atraso
  - Dia +3 (3 dias de atraso)  lembrete final + aviso de BLOQUEIO do carro via app

Como rodar:
    python3 app/notificacoes.py                 # usa a data de hoje
    python3 app/notificacoes.py --data 2026-06-28   # simula outro dia

Por enquanto o envio é só no console (CanalConsole). Quando o WhatsApp Cloud
estiver plugado, troca-se UMA linha (o canal) e tudo continua funcionando.
O link do Pix virá do provedor de pagamento (InfinitePay) — ver DECISOES.md.
"""

import csv
import os
import sys
from datetime import date

from canais import Canal, CanalConsole
from pagamentos import Pagamentos, provedor_padrao

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_COBRANCAS = os.path.join(RAIZ, "dados", "cobrancas.csv")

# Régua de notificações: dias de atraso -> etapa.
REGUA = {0: "vencimento", 1: "atraso_1", 3: "atraso_3_bloqueio"}


def carregar_cobrancas():
    with open(CSV_COBRANCAS, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def formata_reais(valor_txt):
    return "R$ " + f"{float(valor_txt):,.0f}".replace(",", ".")


def formata_data(iso):
    a, m, d = iso.split("-")
    return f"{d}/{m}/{a}"


def montar_mensagem(etapa, c, pix):
    """Monta a mensagem de WhatsApp conforme a etapa da régua. `pix` é o link de pagamento."""
    nome = c["cliente"].split()[0]
    valor = formata_reais(c["valor"])
    venc = formata_data(c["vencimento"])
    ref = c["referente"]

    if etapa == "vencimento":
        return (
            f"Opa {nome}, tudo certo? 👋\n"
            f"Passando pra lembrar que sua mensalidade *{ref}* de {valor} "
            f"vence hoje ({venc}).\n"
            f"É só pagar pelo Pix: {pix}\n"
            f"Qualquer coisa, tô à disposição. Valeu! 🙏"
        )
    if etapa == "atraso_1":
        return (
            f"Oi {nome}, tudo bem? \n"
            f"A cobrança *{ref}* de {valor} venceu ontem ({venc}) e ainda consta "
            f"em aberto.\n"
            f"Consegue regularizar hoje pelo Pix? {pix}\n"
            f"Se já pagou, me avisa pra eu dar baixa. Obrigado! 🙏"
        )
    if etapa == "atraso_3_bloqueio":
        return (
            f"{nome}, a cobrança *{ref}* de {valor} está com *3 dias de atraso* "
            f"(venceu em {venc}).\n"
            f"⚠️ Para evitar o *bloqueio do veículo pelo aplicativo*, peço que "
            f"regularize ainda hoje pelo Pix: {pix}\n"
            f"Se precisar combinar um prazo, me chama que a gente resolve."
        )
    return ""


def rodar(hoje: date, canal: Canal, pagamentos: Pagamentos):
    cobrancas = carregar_cobrancas()

    print("=" * 60)
    print(f"  MOTOR DE NOTIFICAÇÕES — R3nt  (data: {hoje.strftime('%d/%m/%Y')})")
    print("=" * 60)

    enviadas = 0
    for c in cobrancas:
        if c["status"].strip().lower() != "pendente":
            continue  # pagas/canceladas não recebem cobrança

        venc = date.fromisoformat(c["vencimento"])
        dias_atraso = (hoje - venc).days

        etapa = REGUA.get(dias_atraso)
        if etapa is None:
            continue  # hoje não é dia de notificar esta cobrança

        rotulo = {
            "vencimento": "🟢 Vence hoje",
            "atraso_1": "🟡 1 dia de atraso",
            "atraso_3_bloqueio": "🔴 3 dias — aviso de bloqueio",
        }[etapa]
        print(f"\n[{rotulo}] {c['cliente']} — {c['referente']} ({formata_reais(c['valor'])})")
        pix = pagamentos.criar_cobranca(c)  # gera o link de pagamento no provedor
        canal.enviar(c["telefone"], montar_mensagem(etapa, c, pix))
        enviadas += 1

    print("\n" + "-" * 60)
    if enviadas == 0:
        print("Nenhuma notificação para hoje.")
    else:
        print(f"Total de notificações disparadas: {enviadas}")


def main():
    hoje = date.today()
    if "--data" in sys.argv:
        i = sys.argv.index("--data")
        hoje = date.fromisoformat(sys.argv[i + 1])

    rodar(hoje, CanalConsole(), provedor_padrao())


if __name__ == "__main__":
    main()
