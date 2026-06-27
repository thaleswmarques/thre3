#!/usr/bin/env python3
"""
Agente de Triagem (IA) — App R3nt
=================================

O "cérebro" do squad. Recebe uma mensagem que chegou (ex: WhatsApp) e usa a
Claude para:
  1. Identificar QUEM é o contato, cruzando com a base (frota + contas).
  2. Classificar o TIPO (motorista parceiro / cliente locatário / comprador / outro).
  3. Decidir o SETOR de destino (cobranca / frota_manutencao / novos_negocios / atendimento).
  4. Sugerir a próxima ação.

Como rodar:
    export ANTHROPIC_API_KEY="sua-chave"
    python3 app/triagem.py "Oi, é o Marcos do Cactus branco, o carro tá fazendo um barulho"

Sem a chave, ele roda em modo DEMO (mostra o formato da saída sem chamar a IA).

Modelo: claude-opus-4-8 (o mais capaz; a triagem precisa cruzar dados e julgar).
"""

import csv
import os
import sys

MODELO = "claude-opus-4-8"

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_FROTA = os.path.join(RAIZ, "dados", "frota.csv")
CSV_CONTAS = os.path.join(RAIZ, "dados", "contas-a-receber.csv")


def ler_csv(caminho):
    with open(caminho, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def montar_contexto():
    """Resume a base (frota + contas) em texto pra Claude usar na identificação."""
    frota = ler_csv(CSV_FROTA)
    contas = ler_csv(CSV_CONTAS)

    linhas = ["FROTA (nome | modelo | status | locatário/comprador):"]
    for c in frota:
        linhas.append(
            f"- {c['Nome']} | {c['Modelo']} {c.get('Cor','')} | {c['Status']} | {c.get('Locatario') or '—'}"
        )
    linhas.append("\nPESSOAS E CONTAS EM ABERTO:")
    for c in contas:
        if c["Devedor"].upper().startswith("PASSIVO"):
            continue
        linhas.append(f"- {c['Devedor']}: {c['Referente']} = R$ {c['Valor']} ({c['Status']})")
    return "\n".join(linhas)


# Schema da resposta — define exatamente o que a IA deve devolver.
ESQUEMA = {
    "type": "object",
    "properties": {
        "tipo_contato": {
            "type": "string",
            "enum": ["motorista_parceiro", "cliente_locatario", "comprador", "fornecedor", "outro"],
        },
        "pessoa_identificada": {"type": "string"},
        "veiculo_relacionado": {"type": "string"},
        "setor_destino": {
            "type": "string",
            "enum": ["cobranca", "frota_manutencao", "novos_negocios", "atendimento_geral"],
        },
        "confianca": {"type": "string", "enum": ["alta", "media", "baixa"]},
        "resumo": {"type": "string"},
        "proxima_acao": {"type": "string"},
    },
    "required": [
        "tipo_contato", "pessoa_identificada", "veiculo_relacionado",
        "setor_destino", "confianca", "resumo", "proxima_acao",
    ],
    "additionalProperties": False,
}

SYSTEM = """Você é o agente de triagem da R3nt, uma locadora de carros em Confins/MG.
Sua função: ler uma mensagem recebida e identificar quem é o contato cruzando com a
base de dados fornecida, classificar o tipo e encaminhar para o setor certo.

Regras de setor:
- cobranca: cliente/comprador com conta em aberto, ou falando sobre pagamento.
- frota_manutencao: locatário relatando problema/batida/barulho no carro.
- novos_negocios: alguém querendo alugar ou comprar (ainda não é cliente).
- atendimento_geral: não se encaixa nos outros, ou não dá pra identificar.

Se não conseguir identificar a pessoa na base, use pessoa_identificada="desconhecido"
e veiculo_relacionado="—", com confianca="baixa"."""


def triar_com_ia(mensagem, contexto):
    import anthropic

    client = anthropic.Anthropic()
    prompt = (
        f"BASE DE DADOS DA R3NT:\n{contexto}\n\n"
        f"MENSAGEM RECEBIDA:\n\"{mensagem}\"\n\n"
        "Faça a triagem desta mensagem."
    )
    resp = client.messages.create(
        model=MODELO,
        max_tokens=1024,
        system=SYSTEM,
        messages=[{"role": "user", "content": prompt}],
        output_config={"format": {"type": "json_schema", "schema": ESQUEMA}},
    )
    import json
    texto = next(b.text for b in resp.content if b.type == "text")
    return json.loads(texto)


def imprimir(resultado, mensagem):
    print("=" * 60)
    print("  TRIAGEM — R3nt")
    print("=" * 60)
    print(f"Mensagem recebida: \"{mensagem}\"")
    print("-" * 60)
    print(f"👤 Contato........: {resultado['tipo_contato']}")
    print(f"🔎 Pessoa.........: {resultado['pessoa_identificada']}")
    print(f"🚗 Veículo........: {resultado['veiculo_relacionado']}")
    print(f"📍 Encaminhar p/..: {resultado['setor_destino']}")
    print(f"🎯 Confiança......: {resultado['confianca']}")
    print(f"📝 Resumo.........: {resultado['resumo']}")
    print(f"➡️  Próxima ação...: {resultado['proxima_acao']}")


def main():
    mensagem = " ".join(sys.argv[1:]).strip() or \
        "Oi, é o Marcos do Cactus branco, bati o carro ontem à noite, vai precisar de oficina"
    contexto = montar_contexto()

    if not (os.getenv("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_AUTH_TOKEN")):
        print("⚠️  ANTHROPIC_API_KEY não definida — rodando em modo DEMO (sem IA).\n")
        print("Contexto que SERIA enviado à Claude:\n")
        print(contexto)
        print("\nPara rodar de verdade:")
        print('    export ANTHROPIC_API_KEY="sua-chave"')
        print(f'    python3 app/triagem.py "{mensagem}"')
        return

    resultado = triar_com_ia(mensagem, contexto)
    imprimir(resultado, mensagem)


if __name__ == "__main__":
    main()
