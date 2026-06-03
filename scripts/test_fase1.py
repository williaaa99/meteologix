"""
Teste manual da Fase 1 — Scraper

Como rodar:
    docker compose exec bot python scripts/test_fase1.py

O que faz:
    Captura o mapa de hoje do Meteologix e salva em storage/
"""
import sys
from datetime import date
from pathlib import Path

# Garante que o projeto está no path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scraper.scraper import capture_map, build_url

def main():
    hoje = date.today()
    url = build_url(hoje)

    print("[FASE 1] Iniciando captura do mapa...")
    print(f"[FASE 1] Data: {hoje}")
    print(f"[FASE 1] URL: {url}")
    print("[FASE 1] Aguardando mapa carregar (pode levar até 30 segundos)...")

    try:
        output = capture_map(hoje)
        tamanho_kb = output.stat().st_size // 1024
        print(f"[FASE 1] ✓ Mapa capturado com sucesso!")
        print(f"[FASE 1] Arquivo salvo em: {output}")
        print(f"[FASE 1] Tamanho do arquivo: {tamanho_kb} KB")

        if tamanho_kb < 10:
            print("[FASE 1] ⚠️  Arquivo muito pequeno — pode ser screenshot em branco.")
            print("[FASE 1]    Verifique se o mapa carregou corretamente.")
        else:
            print()
            print("FASE 1 OK — Scraper funcionando.")

    except Exception as e:
        print(f"[FASE 1] ✗ Erro: {e}")
        print()
        print("FASE 1 FALHOU — veja o erro acima.")
        sys.exit(1)

if __name__ == "__main__":
    main()
