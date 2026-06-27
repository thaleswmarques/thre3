#!/usr/bin/env python3
"""
Canais de envio — App R3nt
==========================

A "tomada" por onde as mensagens saem. Plugável:
  - CanalConsole ......... imprime na tela (teste offline, sem mandar nada)
  - CanalWhatsAppCloud ... envia de verdade pela API oficial da Meta

Decisão de fornecedor: WhatsApp Cloud API oficial (ver DECISOES.md).
O seletor `canal_padrao()` usa o WhatsApp se houver credencial; senão, o console.
"""

import json
import os
import re
import urllib.request


class Canal:
    """Interface: todo canal sabe enviar uma mensagem para um número."""

    def enviar(self, telefone: str, mensagem: str) -> None:
        raise NotImplementedError


class CanalConsole(Canal):
    """Canal de teste: só imprime o que SERIA enviado. Não manda nada de verdade."""

    def enviar(self, telefone: str, mensagem: str) -> None:
        destino = telefone or "(sem telefone cadastrado)"
        print(f"\n  ┌─ ENVIARIA para {destino}:")
        for linha in mensagem.splitlines():
            print(f"  │ {linha}")
        print("  └─")


def _normalizar_telefone(telefone: str) -> str:
    """Deixa só dígitos e garante o DDI 55 (Brasil). Ex: '(31) 99999-0000' -> '5531999990000'."""
    digitos = re.sub(r"\D", "", telefone or "")
    if not digitos:
        raise ValueError("telefone vazio — não dá para enviar pelo WhatsApp")
    if not digitos.startswith("55"):
        digitos = "55" + digitos
    return digitos


class CanalWhatsAppCloud(Canal):
    """
    Envio pela API oficial do WhatsApp (Meta Cloud API) — esqueleto pronto pra ativar.

    Variáveis de ambiente (configurar como secret, nunca no código):
      WHATSAPP_TOKEN      -> token de acesso da Meta
      WHATSAPP_PHONE_ID   -> ID do número de telefone (Phone Number ID)
      WHATSAPP_VERSAO     -> opcional, padrão "v21.0"

    ⚠️ IMPORTANTE sobre cobrança:
    O WhatsApp só deixa enviar TEXTO livre dentro da janela de 24h depois que o
    cliente te respondeu. Para iniciar a conversa (caso da cobrança), é preciso
    um TEMPLATE de categoria "utility" aprovado pela Meta. Por isso esta classe
    tem os dois caminhos: `enviar` (texto) e `enviar_template`. Em produção, a
    cobrança usa `enviar_template`. Ver DECISOES.md.
    """

    def __init__(self):
        self.token = os.environ["WHATSAPP_TOKEN"]
        self.phone_id = os.environ["WHATSAPP_PHONE_ID"]
        self.versao = os.environ.get("WHATSAPP_VERSAO", "v21.0")

    @property
    def _url(self) -> str:
        return f"https://graph.facebook.com/{self.versao}/{self.phone_id}/messages"

    def _post(self, payload: dict) -> dict:
        req = urllib.request.Request(
            self._url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def enviar(self, telefone: str, mensagem: str) -> None:
        """Envia TEXTO livre. Só funciona dentro da janela de 24h (ver aviso acima)."""
        payload = {
            "messaging_product": "whatsapp",
            "to": _normalizar_telefone(telefone),
            "type": "text",
            "text": {"body": mensagem},
        }
        self._post(payload)

    def enviar_template(self, telefone: str, template: str, idioma: str, variaveis: list) -> None:
        """
        Envia um TEMPLATE aprovado (caminho de produção da cobrança).
        `variaveis` preenche os {{1}}, {{2}}... do template, na ordem.
        """
        componentes = []
        if variaveis:
            componentes = [{
                "type": "body",
                "parameters": [{"type": "text", "text": str(v)} for v in variaveis],
            }]
        payload = {
            "messaging_product": "whatsapp",
            "to": _normalizar_telefone(telefone),
            "type": "template",
            "template": {
                "name": template,
                "language": {"code": idioma},
                "components": componentes,
            },
        }
        self._post(payload)


def canal_padrao() -> Canal:
    """Escolhe o canal: WhatsApp Cloud se houver credencial, senão o console."""
    if os.getenv("WHATSAPP_TOKEN") and os.getenv("WHATSAPP_PHONE_ID"):
        return CanalWhatsAppCloud()
    return CanalConsole()
