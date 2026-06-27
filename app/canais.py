#!/usr/bin/env python3
"""
Canais de envio — App R3nt
==========================

A "tomada" por onde as mensagens saem. Hoje temos só o canal de console (imprime
na tela, pra testar offline). Amanhã, quando você tiver a credencial do WhatsApp,
a gente cria um CanalWhatsAppCloud aqui — e NADA do resto do app muda, porque
todos falam com a mesma interface `Canal`.

Decisão de fornecedor: WhatsApp Cloud API oficial (ver DECISOES.md).
"""


class Canal:
    """Interface: todo canal de envio sabe enviar uma mensagem para um número."""

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


# ---------------------------------------------------------------------------
# FUTURO — quando a credencial do WhatsApp Cloud chegar, descomentar e implementar:
#
# import os, anthropic  # (não, aqui seria o cliente HTTP da Meta)
#
# class CanalWhatsAppCloud(Canal):
#     def __init__(self):
#         self.token = os.environ["WHATSAPP_TOKEN"]
#         self.phone_id = os.environ["WHATSAPP_PHONE_ID"]
#     def enviar(self, telefone, mensagem):
#         # POST para https://graph.facebook.com/v21.0/{phone_id}/messages
#         # com o template de "utility" aprovado (ver DECISOES.md).
#         ...
# ---------------------------------------------------------------------------
