#!/usr/bin/env python3
"""
Agente de Cobrança — App R3nt (primeiro rep do squad)
=====================================================

O que ele faz hoje (MVP):
  1. Lê o arquivo dados/contas-a-receber.csv (a fonte de dados).
  2. Classifica cada conta: ATRASADO, A RECEBER ou EM NEGOCIAÇÃO.
  3. Mostra um resumo do que está em aberto.
  4. Gera a mensagem pronta pro WhatsApp pra cada devedor que dá pra cobrar.

Como rodar (no terminal, dentro da pasta do projeto):
    python3 app/cobranca.py

Sem dependências externas — só Python puro. É de propósito: o primeiro rep
tem que ser simples de entender e de rodar enquanto você aprende dev.
"""

import csv
import os

# Caminho do CSV relativo à raiz do projeto (a pasta que tem o dados/).
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_CONTAS = os.path.join(RAIZ, "dados", "contas-a-receber.csv")


def carregar_contas(caminho):
    """Lê o CSV e devolve uma lista de dicionários (uma linha = uma conta)."""
    with open(caminho, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def valor_em_reais(texto):
    """Converte o campo Valor (texto) em número. Devolve None se não for número."""
    try:
        return float(texto)
    except (ValueError, TypeError):
        return None  # casos como "a definir"


def classificar(conta):
    """Decide o 'balde' de cada conta a partir dos campos Status/Valor."""
    status = (conta.get("Status") or "").lower()
    valor = valor_em_reais(conta.get("Valor"))

    # Passivo: dinheiro que VOCÊ deve devolver (não é cobrança).
    if conta["Devedor"].upper().startswith("PASSIVO") or (valor is not None and valor < 0):
        return "passivo"
    if "negocia" in status or valor is None:
        return "negociacao"
    if "atrasad" in status:
        return "atrasado"
    return "a_receber"


def formata_reais(valor):
    """Formata 1500.0 -> 'R$ 1.500'."""
    return "R$ " + f"{valor:,.0f}".replace(",", ".")


def mensagem_whatsapp(devedor, itens):
    """Monta uma mensagem de cobrança educada agrupando os itens do devedor."""
    primeiro_nome = devedor.split()[0]
    linhas = [f"Opa {primeiro_nome}, tudo certo? 👋", "", "Passando pra alinhar o que está em aberto:"]
    total = 0.0
    for item in itens:
        valor = valor_em_reais(item["Valor"]) or 0.0
        total += valor
        prazo = f" (venc. {item['Prazo']})" if item.get("Prazo") else ""
        linhas.append(f"• {item['Referente']}: {formata_reais(valor)}{prazo}")
    linhas += ["", f"Total: {formata_reais(total)}.",
               "Consegue acertar essa semana? Qualquer coisa a gente combina. Valeu! 🙏"]
    return "\n".join(linhas)


def main():
    contas = carregar_contas(CSV_CONTAS)

    baldes = {"atrasado": [], "a_receber": [], "negociacao": [], "passivo": []}
    for c in contas:
        baldes[classificar(c)].append(c)

    def soma(lista):
        return sum(valor_em_reais(x["Valor"]) or 0.0 for x in lista)

    print("=" * 56)
    print("  AGENTE DE COBRANÇA — R3nt")
    print("=" * 56)
    print(f"🔴 Atrasado:        {formata_reais(soma(baldes['atrasado']))}  ({len(baldes['atrasado'])} conta[s])")
    print(f"🟡 A receber:       {formata_reais(soma(baldes['a_receber']))}  ({len(baldes['a_receber'])} conta[s])")
    print(f"🔄 Em negociação:   {len(baldes['negociacao'])} conta[s] (valor a definir)")
    print(f"⚪ Passivo (devo):  {formata_reais(abs(soma(baldes['passivo'])))}  (caução a devolver)")
    print()

    # Detalhe do que está atrasado — é a prioridade.
    if baldes["atrasado"]:
        print("🔴 ATRASADO (cobrar primeiro):")
        for c in baldes["atrasado"]:
            print(f"   - {c['Devedor']}: {c['Referente']} = {formata_reais(valor_em_reais(c['Valor']))}  [{c['Status']}]")
        print()

    # Mensagens prontas pro WhatsApp: junta atrasado + a_receber por devedor.
    cobraveis = baldes["atrasado"] + baldes["a_receber"]
    por_devedor = {}
    for c in cobraveis:
        por_devedor.setdefault(c["Devedor"], []).append(c)

    print("=" * 56)
    print("  MENSAGENS PRONTAS PRO WHATSAPP")
    print("=" * 56)
    for devedor, itens in por_devedor.items():
        print(f"\n----- {devedor} -----")
        print(mensagem_whatsapp(devedor, itens))


if __name__ == "__main__":
    main()
