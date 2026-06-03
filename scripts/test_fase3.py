"""
Teste manual da Fase 3 — Análise Claude

Como rodar:
    python scripts/test_fase3.py

O que faz:
    Pega as últimas imagens disponíveis em storage/ (ou cria sintéticas),
    envia para o Claude e imprime a análise gerada.

Requisito:
    ANTHROPIC_API_KEY no arquivo .env
"""
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

# Carrega o .env
from dotenv import load_dotenv
load_dotenv()

from PIL import Image
from analyst.analyst import analyse
import tempfile
import unittest.mock as mock
import analyst.analyst as analyst_module


def main():
    print("[FASE 3] Verificando imagens em storage/...")

    storage = Path("storage")
    pngs = sorted(storage.glob("*.png"))

    if len(pngs) >= 4:
        images = pngs[-4:]
        print(f"[FASE 3] Usando {len(images)} imagens reais:")
        for p in images:
            print(f"  - {p.name}")

    else:
        print(f"[FASE 3] Apenas {len(pngs)} imagem(ns) — criando sintéticas para teste.")
        tmp_dir = Path(tempfile.mkdtemp())
        dates = [(date.today() - timedelta(days=3-i)) for i in range(4)]
        images = []
        for d in dates:
            img = Image.new("RGB", (100, 100), color=(80, 130, 190))
            p = tmp_dir / f"{d.isoformat()}.png"
            img.save(p)
            images.append(p)
            print(f"  - {p.name} (sintética)")

    print()
    print("[FASE 3] Enviando imagens para o Claude...")
    print("[FASE 3] Aguarde — pode levar alguns segundos...")
    print()

    try:
        result = analyse(images)
        print("=" * 60)
        print("ANÁLISE GERADA:")
        print("=" * 60)
        print(result)
        print("=" * 60)
        print()
        print("FASE 3 OK — Análise Claude funcionando.")

    except Exception as e:
        print(f"[FASE 3] ✗ Erro: {e}")
        print()
        if "api_key" in str(e).lower() or "auth" in str(e).lower():
            print("Verifique se ANTHROPIC_API_KEY está configurada no arquivo .env")
        print("FASE 3 FALHOU — veja o erro acima.")
        sys.exit(1)


if __name__ == "__main__":
    main()
