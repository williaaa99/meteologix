"""
Teste manual da Fase 4 — Envio WhatsApp

Como rodar:
    python scripts/test_fase4.py

O que faz:
    Envia uma mensagem de texto de teste para o grupo configurado no .env
    para confirmar que a conexão com a Evolution API está funcionando.

Requisitos:
    - EVOLUTION_API_URL no .env
    - EVOLUTION_API_KEY no .env
    - EVOLUTION_INSTANCE no .env
    - WHATSAPP_GROUP_ID no .env
    - Evolution API rodando e WhatsApp conectado
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

import config
from whatsapp.whatsapp import send_text


def main():
    print("[FASE 4] Configuração carregada:")
    print(f"  EVOLUTION_API_URL : {config.EVOLUTION_API_URL}")
    print(f"  EVOLUTION_INSTANCE: {config.EVOLUTION_INSTANCE}")
    print(f"  WHATSAPP_GROUP_ID : {config.WHATSAPP_GROUP_ID}")
    print()
    print("[FASE 4] Enviando mensagem de teste...")

    try:
        send_text("🤖 Meteologix Bot — teste de conexão OK!")
        print("[FASE 4] ✓ Mensagem enviada com sucesso!")
        print()
        print("FASE 4 OK — WhatsApp funcionando.")
        print("Verifique se a mensagem chegou no grupo.")

    except Exception as e:
        print(f"[FASE 4] ✗ Erro: {e}")
        print()
        print("Possíveis causas:")
        print("  1. EVOLUTION_INSTANCE errado — verifique o nome no painel")
        print("  2. WHATSAPP_GROUP_ID errado — verifique o ID do grupo")
        print("  3. Evolution API não está rodando")
        print("  4. WhatsApp desconectado — reconecte no painel")
        print()
        print("FASE 4 FALHOU — veja o erro acima.")
        sys.exit(1)


if __name__ == "__main__":
    main()
