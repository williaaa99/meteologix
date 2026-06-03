# Design Spec — Meteologix Corn Weather Bot

**Date:** 2026-05-28  
**Status:** Approved  
**Author:** Brainstorming session with Willian

---

## 1. Overview

Automated system that runs Monday–Friday at 08:00 BRT on a 24/7 server. Each day it captures the accumulated precipitation forecast map from Meteologix for Brazil, accumulates 4 consecutive days of maps, assembles them into an animated GIF, generates a corn-commodity-focused weather analysis via Claude API, and sends both the GIF and analysis to a WhatsApp group serving corn traders.

---

## 2. Goals

- Deliver a daily morning weather briefing tailored for corn commodity traders
- Visualize how the 15-day precipitation forecast has evolved over the last 4 days
- Focus analysis on Brazil's main corn-producing regions: Mato Grosso, Paraná, Goiás, Mato Grosso do Sul, Minas Gerais, Rio Grande do Sul, and MATOPIBA (Maranhão, Tocantins, Piauí, Bahia)
- Support future expansion to individual WhatsApp contact delivery with minimal changes

---

## 3. Non-Goals

- Does not support other crops (soybeans, sugarcane, etc.) in this version
- Does not store historical analysis texts (only images are persisted)
- Does not provide a web dashboard or API endpoint

---

## 4. Architecture

### 4.1 Project Structure

```
meteologix-corn-bot/
├── scraper/
│   └── scraper.py          # Playwright-based map capture
├── gif_maker/
│   └── gif_maker.py        # Assembles last 4 images into GIF
├── analyst/
│   └── analyst.py          # Claude API vision analysis
├── whatsapp/
│   └── whatsapp.py         # Evolution API REST client
├── scheduler/
│   └── scheduler.py        # APScheduler orchestrator
├── storage/                # Persisted daily map images + latest.gif
├── config.py               # Loads .env variables
├── main.py                 # Entrypoint
├── .env                    # Secrets (not committed)
├── Dockerfile
└── docker-compose.yml
```

### 4.2 Docker Containers

| Container      | Image                        | Purpose                          |
|----------------|------------------------------|----------------------------------|
| `bot`          | Python 3.12 + Playwright     | All bot modules                  |
| `evolution-api`| `atendai/evolution-api`      | WhatsApp non-official automation |
| `redis`        | `redis:7-alpine`             | Evolution API session store      |

---

## 5. Module Design

### 5.1 Scraper (`scraper/scraper.py`)

**Responsibility:** Capture the daily precipitation map from Meteologix and save it to `storage/`.

**URL Pattern:**
```
https://meteologix.com/br/model-charts/standard/brazil/accumulated-precipitation/YYYYMMDD-0600z.html
```
The date is generated from the current date at runtime.

**Playwright Logic:**
1. Launch headless Chromium
2. Navigate to the day's URL
3. Wait for the map element selector to be fully visible and rendered (timeout: 30s) — this ensures state borders, capital city labels, color legend, and all map overlays are present
4. Screenshot only the map element (`locator.screenshot()`) — not the full page
5. Save as `storage/YYYY-MM-DD.png`

**Error Handling:** If map fails to load within 30s, log the error and skip the day. The scheduler always saves the image when available; GIF generation and analysis only proceed when 4 or more images are present in `storage/`.

**Dependencies:** `playwright`, `playwright install chromium`

---

### 5.2 GIF Maker (`gif_maker/gif_maker.py`)

**Responsibility:** Compose the last 4 accumulated daily images into an animated GIF.

**Logic:**
1. Read all `.png` files in `storage/`, sort by filename (date)
2. Take the 4 most recent images
3. For each image, overlay a date label (e.g., "Seg 09/Jun") in the bottom-left corner using `Pillow` — white text with dark shadow for readability against the map background
4. Export as `storage/latest.gif` with:
   - Frame duration: 1500ms per frame
   - Loop: infinite
5. Overwrite `latest.gif` on every execution

**Dependencies:** `Pillow`

---

### 5.3 Analyst (`analyst/analyst.py`)

**Responsibility:** Send the 4 daily images to Claude API and receive a corn-commodity-focused weather analysis.

**Model:** `claude-3-5-sonnet-latest` (vision capable)

**System Prompt:**
> Você é um especialista em meteorologia aplicada a commodities agrícolas. Analise mapas de precipitação acumulada do Brasil focando nas principais regiões produtoras de milho: Mato Grosso, Paraná, Goiás, Mato Grosso do Sul, Minas Gerais, Rio Grande do Sul e MATOPIBA (Maranhão, Tocantins, Piauí e Bahia).

**User Prompt:**
> Estas são as previsões de precipitação acumulada dos últimos 4 dias consecutivos. Analise a evolução e gere um relatório objetivo para traders de milho contendo:
> 1. **Tendência de chuva por região produtora** — a previsão está melhorando ou piorando?
> 2. **Impacto potencial na cultura** — estresse hídrico, risco de atraso no plantio/colheita, condições favoráveis
> 3. **Implicação para preços** — alta de risco se chuva escassa/excesso, pressão de baixa se chuva ideal
>
> Seja direto, use linguagem de mercado, responda em português.

**Input:** 4 images encoded as base64, passed as `image_url` blocks in the messages array.

**Output:** String with the analysis text, passed to the WhatsApp module.

**Dependencies:** `anthropic`

---

### 5.4 WhatsApp (`whatsapp/whatsapp.py`)

**Responsibility:** Send the GIF and analysis text to the configured WhatsApp group via Evolution API.

**Sequence:**
1. `POST /message/sendMedia` — sends `storage/latest.gif` as a document/animation with caption containing the analysis text
2. Alternatively, if the GIF + text caption exceeds limits: send GIF first, then `POST /message/sendText` with the analysis

**Future Individual Sending:**  
A `recipients` list in `config.py` will accept both group IDs and individual phone numbers. The same REST call handles both — only the `to` field changes. Enabling individual delivery requires adding numbers to this list, no structural changes needed.

**Dependencies:** `httpx` or `requests`

---

### 5.5 Scheduler (`scheduler/scheduler.py`)

**Responsibility:** Orchestrate all modules on a Monday–Friday 08:00 BRT schedule.

```python
scheduler.add_job(
    run_daily_job,
    'cron',
    day_of_week='mon-fri',
    hour=8,
    minute=0,
    timezone='America/Sao_Paulo'
)
```

**`run_daily_job` sequence:**
1. Run scraper → save today's image
2. Check image count in `storage/` → if fewer than 4, log and skip GIF/analysis (still saves image for future days)
3. Run gif_maker → generate `latest.gif`
4. Run analyst → get analysis text
5. Run whatsapp → send GIF + text
6. On any module failure: log error + send a plain-text alert to the WhatsApp group

**Dependencies:** `APScheduler`

---

## 6. Configuration

**`.env` file (never committed to git):**
```
ANTHROPIC_API_KEY=sk-ant-...
EVOLUTION_API_URL=http://evolution-api:8080
EVOLUTION_API_KEY=your-evolution-key
EVOLUTION_INSTANCE=meteologix-bot
WHATSAPP_GROUP_ID=xxxxxxxxxxx@g.us
```

**`config.py`** reads all variables via `python-dotenv` and exposes them as typed constants. Future individual recipients are added here as a list.

---

## 7. First-Time Setup

1. Clone repo and fill `.env`
2. Run `docker-compose up -d`
3. Access Evolution API panel at `http://localhost:8080` → scan WhatsApp QR Code once → session persists permanently
4. Bot runs automatically from 08:00 BRT on the first business day

---

## 8. Error Handling Summary

| Failure Point        | Behavior                                              |
|----------------------|-------------------------------------------------------|
| Meteologix timeout   | Skip day, log error, continue accumulation            |
| Fewer than 4 images  | Save image only, skip GIF/analysis/send               |
| Claude API error     | Send GIF only with fallback text noting analysis failure |
| Evolution API error  | Log error, retry once after 5 minutes                 |
| Scheduler crash      | Docker restart policy `always` brings bot back up     |

---

## 9. Dependencies Summary

```
anthropic
playwright
Pillow
APScheduler
python-dotenv
httpx
```

---

## 10. Future Expansion

- **Individual sending:** add phone numbers to `WHATSAPP_RECIPIENTS` list in `.env`
- **Multiple crop types:** add new analyst prompt profiles (soy, cotton, etc.)
- **Multiple map types:** extend scraper to capture wind, temperature maps alongside precipitation
- **Historical storage:** add SQLite or JSON log of daily analysis texts
