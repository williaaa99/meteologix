"""
Teste manual da Fase 2 — GIF Maker

Como rodar:
    python scripts/test_fase2.py

O que faz:
    Cria 4 imagens de teste, monta o GIF animado e abre para visualizar.
"""
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from PIL import Image
from gif_maker.gif_maker import make_gif, get_label
import os
import tempfile


def main():
    print("[FASE 2] Verificando imagens em storage/...")

    storage = Path("storage")
    pngs = sorted(storage.glob("*.png"))

    if len(pngs) >= 4:
        # Usa imagens reais do storage
        print(f"[FASE 2] {len(pngs)} imagens encontradas — usando as últimas 4 reais.")
        output = storage / "test_fase2.gif"
        result = make_gif(output_path=output)
        print(f"[FASE 2] ✓ GIF criado: {result}")
        print(f"[FASE 2] Tamanho: {result.stat().st_size // 1024} KB")
        print()
        print("FASE 2 OK — GIF Maker funcionando com imagens reais.")
        print(f"Abra o arquivo para visualizar: {result.resolve()}")

    else:
        # Cria imagens de teste sintéticas
        print(f"[FASE 2] Apenas {len(pngs)} imagem(ns) em storage/ — criando 4 sintéticas para teste.")

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            colors = [(100, 150, 200), (120, 170, 210), (80, 130, 190), (60, 110, 180)]
            dates = [(date.today() - timedelta(days=3-i)) for i in range(4)]

            for d, color in zip(dates, colors):
                img = Image.new("RGB", (760, 760), color=color)
                img.save(tmp_path / f"{d.isoformat()}.png")
                print(f"[FASE 2]   Criada imagem sintética: {d.isoformat()}.png")

            output = Path("storage") / "test_fase2.gif"
            output.parent.mkdir(exist_ok=True)

            # Patch config para apontar para tmp
            import gif_maker.gif_maker as gm_module
            import unittest.mock as mock
            mock_config = mock.MagicMock()
            mock_config.STORAGE_DIR = str(tmp_path)

            with mock.patch.object(gm_module, "config", mock_config):
                result = make_gif(output_path=output)

            print(f"[FASE 2] ✓ GIF criado: {result}")
            print(f"[FASE 2] Tamanho: {result.stat().st_size // 1024} KB")
            print()
            print("FASE 2 OK — GIF Maker funcionando (imagens sintéticas).")
            print(f"Abra o arquivo para visualizar: {result.resolve()}")
            print()
            print("NOTA: Rode a Fase 1 por 4 dias seguidos para testar com imagens reais.")


if __name__ == "__main__":
    main()
