from __future__ import annotations

import base64
from pathlib import Path

import anthropic

import config

SYSTEM_PROMPT = (
    "Você é um especialista em meteorologia aplicada a commodities agrícolas. "
    "Analise mapas de precipitação acumulada do Brasil focando nas principais regiões "
    "produtoras de milho: Mato Grosso, Paraná, Goiás, Mato Grosso do Sul, Minas Gerais, "
    "Rio Grande do Sul e MATOPIBA (Maranhão, Tocantins, Piauí e Bahia)."
)

USER_PROMPT = (
    "Estas são as previsões de precipitação acumulada dos últimos 4 dias consecutivos. "
    "Analise a evolução e gere um relatório objetivo para traders de milho contendo:\n"
    "1. *Tendência de chuva por região produtora* — a previsão está melhorando ou piorando?\n"
    "2. *Impacto potencial na cultura* — estresse hídrico, risco de atraso no plantio/colheita, "
    "condições favoráveis\n"
    "3. *Implicação para preços* — alta de risco se chuva escassa/excesso, pressão de baixa "
    "se chuva ideal\n\n"
    "Seja direto, use linguagem de mercado, responda em português."
)


def encode_image(path: Path) -> str:
    """Return base64-encoded content of the given image file."""
    return base64.standard_b64encode(path.read_bytes()).decode("utf-8")


def analyse(image_paths: list[Path]) -> str:
    """Send 4 map images to Claude and return corn-focused weather analysis.

    Args:
        image_paths: List of exactly 4 PNG file paths, ordered oldest -> newest.

    Returns:
        Analysis text string in Portuguese.
    """
    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

    image_blocks = [
        {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": "image/png",
                "data": encode_image(p),
            },
        }
        for p in image_paths
    ]

    message = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": image_blocks + [{"type": "text", "text": USER_PROMPT}],
            }
        ],
    )
    return message.content[0].text
