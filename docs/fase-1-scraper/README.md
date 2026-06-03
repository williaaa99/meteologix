# Fase 1 — Scraper

## O que faz

Abre o site do Meteologix em um navegador headless (sem janela), espera o mapa de precipitação carregar e tira um screenshot da área do mapa.

O arquivo é salvo na pasta `storage/` com o nome da data: `2026-06-01.png`.

## Como funciona

```
Meteologix (site) → Playwright (navegador headless) → screenshot → storage/YYYY-MM-DD.png
```

O site usa JavaScript para renderizar o mapa (Leaflet.js), por isso precisamos de um navegador real — não dá para baixar o HTML simplesmente.

## Arquivos

| Arquivo | O que faz |
|---------|-----------|
| `scraper/scraper.py` | Lógica principal: monta a URL, abre o navegador, tira o screenshot |
| `scripts/test_fase1.py` | Script de teste manual — rode para validar esta fase |

## Como testar

Na VPS, com os containers rodando:

```bash
docker compose exec bot python scripts/test_fase1.py
```

### O que esperar

```
[FASE 1] Iniciando captura do mapa...
[FASE 1] URL: https://meteologix.com/br/model-charts/standard/brazil/accumulated-precipitation/20260601-0600z.html
[FASE 1] Aguardando mapa carregar (pode levar até 30 segundos)...
[FASE 1] ✓ Mapa capturado com sucesso!
[FASE 1] Arquivo salvo em: storage/2026-06-01.png
[FASE 1] Tamanho do arquivo: 245 KB

FASE 1 OK — Scraper funcionando.
```

### Verificar a imagem

Para confirmar que a imagem está correta (não em branco):

```bash
docker compose exec bot python -c "
from PIL import Image
img = Image.open('storage/2026-06-01.png')
print('Tamanho:', img.size)
print('Modo:', img.mode)
"
```

Deve retornar algo como `Tamanho: (1280, 900)`.

## Possíveis erros

| Erro | Causa | Solução |
|------|-------|---------|
| `Timeout 30s` | Site lento ou mapa não carregou | Rode novamente — pode ser instabilidade |
| `storage/ not found` | Pasta não existe | `mkdir -p storage` |
| `net::ERR_NAME_NOT_RESOLVED` | VPS sem internet | Verifique conexão do container |

## Próxima fase

Quando esta fase estiver OK → [Fase 2 — GIF Maker](../fase-2-gif/README.md)
