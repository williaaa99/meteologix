# Meteologix Corn Weather Bot Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an automated Python bot that captures daily precipitation forecast maps from Meteologix, assembles 4-day animated GIFs, generates corn-commodity weather analysis via Claude API, and delivers both to a WhatsApp group Monday–Friday at 08:00 BRT.

**Architecture:** Modular Python package with independent `scraper`, `gif_maker`, `analyst`, and `whatsapp` modules orchestrated by APScheduler. Evolution API handles WhatsApp delivery via REST. All services run via docker-compose on a 24/7 server.

**Tech Stack:** Python 3.12, Playwright (Chromium headless), Pillow, anthropic SDK, httpx, APScheduler, Evolution API, Redis, Docker

---

## File Map

| File | Responsibility |
|------|---------------|
| `config.py` | Load and expose all env vars as typed constants |
| `scraper/scraper.py` | Build Meteologix URL, launch headless Chromium, screenshot map element, save to storage |
| `gif_maker/gif_maker.py` | Read last 4 PNGs, overlay date labels, export animated GIF |
| `analyst/analyst.py` | Encode images as base64, call Claude API, return analysis string |
| `whatsapp/whatsapp.py` | REST client for Evolution API — send GIF and text |
| `scheduler/scheduler.py` | APScheduler cron job, orchestrates all modules, handles errors |
| `main.py` | Entrypoint — starts the scheduler |
| `tests/test_config.py` | Verify config raises on missing vars |
| `tests/test_scraper.py` | Unit-test URL builder; mock Playwright for capture test |
| `tests/test_gif_maker.py` | Unit-test label builder; integration-test GIF with real tiny PNGs |
| `tests/test_analyst.py` | Mock anthropic client, test prompt construction and return value |
| `tests/test_whatsapp.py` | Mock httpx, test payload shape and raise_for_status |
| `tests/test_scheduler.py` | Mock all modules, test orchestration logic and error branches |
| `requirements.txt` | Python dependencies |
| `.env.example` | Template for secrets |
| `Dockerfile` | Python 3.12 + Playwright Chromium |
| `docker-compose.yml` | bot + evolution-api + redis |

---

## Task 1: Project Scaffolding

**Files:**
- Create: `requirements.txt`
- Create: `.env.example`
- Create: `config.py`
- Create: `tests/__init__.py`
- Create: `scraper/__init__.py`
- Create: `gif_maker/__init__.py`
- Create: `analyst/__init__.py`
- Create: `whatsapp/__init__.py`
- Create: `scheduler/__init__.py`
- Create: `storage/.gitkeep`

- [ ] **Step 1: Create directory structure**

```bash
mkdir -p scraper gif_maker analyst whatsapp scheduler storage tests
touch scraper/__init__.py gif_maker/__init__.py analyst/__init__.py \
      whatsapp/__init__.py scheduler/__init__.py tests/__init__.py \
      storage/.gitkeep
```

- [ ] **Step 2: Create `requirements.txt`**

```
anthropic>=0.25.0
playwright>=1.44.0
Pillow>=10.3.0
APScheduler>=3.10.4
httpx>=0.27.0
python-dotenv>=1.0.1
pytest>=8.2.0
pytest-mock>=3.14.0
```

- [ ] **Step 3: Create `.env.example`**

```
ANTHROPIC_API_KEY=sk-ant-...
EVOLUTION_API_URL=http://evolution-api:8080
EVOLUTION_API_KEY=your-evolution-key-here
EVOLUTION_INSTANCE=meteologix-bot
WHATSAPP_GROUP_ID=xxxxxxxxxxx@g.us
STORAGE_DIR=storage
```

- [ ] **Step 4: Create `.gitignore`**

```
.env
storage/*.png
storage/*.gif
__pycache__/
*.pyc
.pytest_cache/
```

- [ ] **Step 5: Install dependencies**

```bash
pip install -r requirements.txt
playwright install chromium
```

Expected: all packages install without errors.

- [ ] **Step 6: Commit**

```bash
git init
git add .
git commit -m "chore: scaffold project structure"
```

---

## Task 2: Config Module

**Files:**
- Create: `config.py`
- Create: `tests/test_config.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_config.py
import os
import importlib
import pytest

def test_config_raises_on_missing_required_var(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("EVOLUTION_API_KEY", raising=False)
    monkeypatch.delenv("WHATSAPP_GROUP_ID", raising=False)
    # Reload config without the required vars — should raise KeyError
    import config
    with pytest.raises(KeyError):
        importlib.reload(config)

def test_config_storage_dir_has_default(monkeypatch, tmp_path):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setenv("EVOLUTION_API_KEY", "evo-key")
    monkeypatch.setenv("WHATSAPP_GROUP_ID", "123@g.us")
    monkeypatch.delenv("STORAGE_DIR", raising=False)
    import config
    importlib.reload(config)
    assert config.STORAGE_DIR == "storage"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_config.py -v
```

Expected: `ModuleNotFoundError` or `AttributeError` — config.py doesn't exist yet.

- [ ] **Step 3: Create `config.py`**

```python
# config.py
import os
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY: str = os.environ["ANTHROPIC_API_KEY"]
EVOLUTION_API_URL: str = os.environ.get("EVOLUTION_API_URL", "http://localhost:8080")
EVOLUTION_API_KEY: str = os.environ["EVOLUTION_API_KEY"]
EVOLUTION_INSTANCE: str = os.environ.get("EVOLUTION_INSTANCE", "meteologix-bot")
WHATSAPP_GROUP_ID: str = os.environ["WHATSAPP_GROUP_ID"]
STORAGE_DIR: str = os.environ.get("STORAGE_DIR", "storage")
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_config.py -v
```

Expected: 2 PASSED

- [ ] **Step 5: Commit**

```bash
git add config.py tests/test_config.py
git commit -m "feat: add config module with env validation"
```

---

## Task 3: Scraper Module

**Files:**
- Create: `scraper/scraper.py`
- Create: `tests/test_scraper.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_scraper.py
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from scraper.scraper import build_url, capture_map


def test_build_url_formats_date_correctly():
    d = date(2026, 6, 13)
    url = build_url(d)
    assert url == (
        "https://meteologix.com/br/model-charts/standard/brazil/"
        "accumulated-precipitation/20260613-0600z.html"
    )


def test_build_url_zero_pads_month_and_day():
    d = date(2026, 1, 5)
    url = build_url(d)
    assert "20260105-0600z" in url


def test_capture_map_saves_file(tmp_path, monkeypatch):
    monkeypatch.setattr("config.STORAGE_DIR", str(tmp_path))

    mock_element = MagicMock()
    mock_page = MagicMock()
    mock_page.wait_for_selector.return_value = mock_element
    mock_browser = MagicMock()
    mock_browser.new_page.return_value = mock_page
    mock_playwright_ctx = MagicMock()
    mock_playwright_ctx.__enter__ = MagicMock(return_value=mock_playwright_ctx)
    mock_playwright_ctx.__exit__ = MagicMock(return_value=False)
    mock_playwright_ctx.chromium.launch.return_value = mock_browser

    with patch("scraper.scraper.sync_playwright", return_value=mock_playwright_ctx):
        result = capture_map(date(2026, 6, 13))

    assert result == tmp_path / "2026-06-13.png"
    mock_element.screenshot.assert_called_once_with(path=str(tmp_path / "2026-06-13.png"))


def test_capture_map_raises_on_timeout(tmp_path, monkeypatch):
    monkeypatch.setattr("config.STORAGE_DIR", str(tmp_path))

    mock_page = MagicMock()
    mock_page.wait_for_selector.side_effect = Exception("Timeout")
    mock_browser = MagicMock()
    mock_browser.new_page.return_value = mock_page
    mock_playwright_ctx = MagicMock()
    mock_playwright_ctx.__enter__ = MagicMock(return_value=mock_playwright_ctx)
    mock_playwright_ctx.__exit__ = MagicMock(return_value=False)
    mock_playwright_ctx.chromium.launch.return_value = mock_browser

    with patch("scraper.scraper.sync_playwright", return_value=mock_playwright_ctx):
        with pytest.raises(Exception, match="Timeout"):
            capture_map(date(2026, 6, 13))
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_scraper.py -v
```

Expected: `ImportError` — scraper.py doesn't exist yet.

- [ ] **Step 3: Create `scraper/scraper.py`**

```python
# scraper/scraper.py
from datetime import date
from pathlib import Path

from playwright.sync_api import sync_playwright

import config

# Meteologix uses Leaflet.js — this is the standard container selector.
# If the map doesn't render, open the page in a browser and inspect to confirm.
MAP_SELECTOR = ".leaflet-container"
TIMEOUT_MS = 30_000


def build_url(target_date: date) -> str:
    """Return the Meteologix precipitation URL for the given date."""
    return (
        "https://meteologix.com/br/model-charts/standard/brazil/"
        f"accumulated-precipitation/{target_date.strftime('%Y%m%d')}-0600z.html"
    )


def capture_map(target_date: date | None = None) -> Path:
    """Launch headless Chromium, screenshot the map element, save to storage.

    Args:
        target_date: Date to capture. Defaults to today.

    Returns:
        Path to the saved PNG file.

    Raises:
        Exception: If map element does not load within TIMEOUT_MS.
    """
    if target_date is None:
        target_date = date.today()

    url = build_url(target_date)
    output_path = Path(config.STORAGE_DIR) / f"{target_date.isoformat()}.png"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        page.goto(url, timeout=TIMEOUT_MS)
        page.wait_for_load_state("networkidle", timeout=TIMEOUT_MS)
        map_element = page.wait_for_selector(MAP_SELECTOR, timeout=TIMEOUT_MS)
        map_element.screenshot(path=str(output_path))
        browser.close()

    return output_path
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_scraper.py -v
```

Expected: 4 PASSED

- [ ] **Step 5: Commit**

```bash
git add scraper/scraper.py tests/test_scraper.py
git commit -m "feat: add scraper module with Playwright map capture"
```

---

## Task 4: GIF Maker Module

**Files:**
- Create: `gif_maker/gif_maker.py`
- Create: `tests/test_gif_maker.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_gif_maker.py
from pathlib import Path
from PIL import Image
import pytest

from gif_maker.gif_maker import get_label, make_gif


def test_get_label_formats_weekday_and_date():
    # 2026-06-13 is a Saturday (Sáb)
    assert get_label("2026-06-13.png") == "Sáb 13/06"


def test_get_label_monday():
    # 2026-06-08 is a Monday (Seg)
    assert get_label("2026-06-08.png") == "Seg 08/06"


def test_get_label_returns_empty_for_invalid():
    assert get_label("nodate.png") == ""


def test_make_gif_creates_file(tmp_path, monkeypatch):
    monkeypatch.setattr("config.STORAGE_DIR", str(tmp_path))

    # Create 4 minimal valid PNG files with date-like names
    dates = ["2026-06-09", "2026-06-10", "2026-06-11", "2026-06-12"]
    for d in dates:
        img = Image.new("RGB", (100, 80), color=(100, 150, 200))
        img.save(tmp_path / f"{d}.png")

    output = tmp_path / "test_output.gif"
    result = make_gif(output_path=output)

    assert result == output
    assert output.exists()


def test_make_gif_raises_when_fewer_than_4_images(tmp_path, monkeypatch):
    monkeypatch.setattr("config.STORAGE_DIR", str(tmp_path))

    img = Image.new("RGB", (100, 80), color=(100, 150, 200))
    img.save(tmp_path / "2026-06-09.png")

    with pytest.raises(ValueError, match="Need 4 images"):
        make_gif()


def test_make_gif_uses_last_4_when_more_available(tmp_path, monkeypatch):
    monkeypatch.setattr("config.STORAGE_DIR", str(tmp_path))

    dates = ["2026-06-07", "2026-06-08", "2026-06-09", "2026-06-10", "2026-06-11"]
    for d in dates:
        img = Image.new("RGB", (100, 80), color=(100, 150, 200))
        img.save(tmp_path / f"{d}.png")

    output = tmp_path / "test_output.gif"
    result = make_gif(output_path=output)
    assert result.exists()  # used 4 of the 5 — no error
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_gif_maker.py -v
```

Expected: `ImportError` — gif_maker.py doesn't exist yet.

- [ ] **Step 3: Create `gif_maker/gif_maker.py`**

```python
# gif_maker/gif_maker.py
import re
from datetime import date
from pathlib import Path

from PIL import Image, ImageDraw

import config

WEEKDAY_PT = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
FRAME_DURATION_MS = 1500


def get_label(filename: str) -> str:
    """Extract date from a 'YYYY-MM-DD.png' filename and return 'Seg DD/MM'."""
    match = re.search(r"(\d{4}-\d{2}-\d{2})", filename)
    if not match:
        return ""
    d = date.fromisoformat(match.group(1))
    return f"{WEEKDAY_PT[d.weekday()]} {d.day:02d}/{d.month:02d}"


def _overlay_label(img: Image.Image, label: str) -> Image.Image:
    """Draw a white label with black shadow in the bottom-left corner."""
    draw = ImageDraw.Draw(img)
    x, y = 10, img.height - 30
    draw.text((x + 1, y + 1), label, fill="black")  # shadow
    draw.text((x, y), label, fill="white")
    return img


def make_gif(output_path: Path | None = None) -> Path:
    """Compose the last 4 saved PNGs into an animated GIF.

    Args:
        output_path: Destination path for the GIF. Defaults to storage/latest.gif.

    Returns:
        Path to the generated GIF.

    Raises:
        ValueError: If fewer than 4 PNG images are found in storage.
    """
    storage = Path(config.STORAGE_DIR)
    images = sorted(storage.glob("*.png"))[-4:]

    if len(images) < 4:
        raise ValueError(f"Need 4 images, found {len(images)}")

    if output_path is None:
        output_path = storage / "latest.gif"

    frames: list[Image.Image] = []
    for img_path in images:
        img = Image.open(img_path).convert("RGB")
        label = get_label(img_path.name)
        if label:
            img = _overlay_label(img, label)
        frames.append(img)

    frames[0].save(
        output_path,
        save_all=True,
        append_images=frames[1:],
        duration=FRAME_DURATION_MS,
        loop=0,
        format="GIF",
    )
    return output_path
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_gif_maker.py -v
```

Expected: 5 PASSED

- [ ] **Step 5: Commit**

```bash
git add gif_maker/gif_maker.py tests/test_gif_maker.py
git commit -m "feat: add gif_maker module with date label overlay"
```

---

## Task 5: Analyst Module

**Files:**
- Create: `analyst/analyst.py`
- Create: `tests/test_analyst.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_analyst.py
from pathlib import Path
from unittest.mock import MagicMock, patch
from PIL import Image
import pytest

from analyst.analyst import encode_image, analyse


def test_encode_image_returns_base64_string(tmp_path):
    img = Image.new("RGB", (10, 10), color=(255, 0, 0))
    p = tmp_path / "test.png"
    img.save(p)
    result = encode_image(p)
    import base64
    # Should be valid base64
    decoded = base64.standard_b64decode(result)
    assert len(decoded) > 0


def test_analyse_calls_claude_with_4_image_blocks(tmp_path, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

    # Create 4 tiny PNG files
    paths = []
    for i in range(4):
        img = Image.new("RGB", (10, 10), color=(i * 60, 100, 200))
        p = tmp_path / f"img_{i}.png"
        img.save(p)
        paths.append(p)

    mock_message = MagicMock()
    mock_message.content = [MagicMock(text="Análise de teste para traders.")]
    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_message

    with patch("analyst.analyst.anthropic.Anthropic", return_value=mock_client):
        result = analyse(paths)

    assert result == "Análise de teste para traders."

    call_kwargs = mock_client.messages.create.call_args.kwargs
    user_content = call_kwargs["messages"][0]["content"]
    image_blocks = [b for b in user_content if b.get("type") == "image"]
    assert len(image_blocks) == 4
    assert call_kwargs["model"] == "claude-3-5-sonnet-latest"


def test_analyse_includes_corn_regions_in_prompt(tmp_path, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

    paths = []
    for i in range(4):
        img = Image.new("RGB", (10, 10))
        p = tmp_path / f"img_{i}.png"
        img.save(p)
        paths.append(p)

    mock_message = MagicMock()
    mock_message.content = [MagicMock(text="ok")]
    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_message

    with patch("analyst.analyst.anthropic.Anthropic", return_value=mock_client):
        analyse(paths)

    call_kwargs = mock_client.messages.create.call_args.kwargs
    system = call_kwargs["system"]
    assert "Mato Grosso" in system
    assert "MATOPIBA" in system
    assert "Paraná" in system
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_analyst.py -v
```

Expected: `ImportError` — analyst.py doesn't exist yet.

- [ ] **Step 3: Create `analyst/analyst.py`**

```python
# analyst/analyst.py
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
        image_paths: List of exactly 4 PNG file paths, ordered oldest → newest.

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
        model="claude-3-5-sonnet-latest",
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
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_analyst.py -v
```

Expected: 3 PASSED

- [ ] **Step 5: Commit**

```bash
git add analyst/analyst.py tests/test_analyst.py
git commit -m "feat: add analyst module with Claude corn-focused weather analysis"
```

---

## Task 6: WhatsApp Module

**Files:**
- Create: `whatsapp/whatsapp.py`
- Create: `tests/test_whatsapp.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_whatsapp.py
from pathlib import Path
from unittest.mock import MagicMock, patch
from PIL import Image
import httpx
import pytest

from whatsapp.whatsapp import send_gif, send_text


def _setup_env(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test")
    monkeypatch.setenv("EVOLUTION_API_KEY", "evo-test")
    monkeypatch.setenv("EVOLUTION_API_URL", "http://localhost:8080")
    monkeypatch.setenv("EVOLUTION_INSTANCE", "test-bot")
    monkeypatch.setenv("WHATSAPP_GROUP_ID", "group123@g.us")


def test_send_gif_posts_to_correct_endpoint(tmp_path, monkeypatch):
    _setup_env(monkeypatch)
    import importlib, config
    importlib.reload(config)

    gif_path = tmp_path / "latest.gif"
    gif_path.write_bytes(b"GIF89a")  # minimal fake gif bytes

    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()

    with patch("whatsapp.whatsapp.httpx.post", return_value=mock_response) as mock_post:
        send_gif(gif_path, caption="análise teste")

    mock_post.assert_called_once()
    call_kwargs = mock_post.call_args
    assert "sendMedia/test-bot" in call_kwargs.args[0]
    payload = call_kwargs.kwargs["json"]
    assert payload["number"] == "group123@g.us"
    assert payload["caption"] == "análise teste"
    assert payload["mimetype"] == "image/gif"
    mock_response.raise_for_status.assert_called_once()


def test_send_gif_accepts_custom_recipient(tmp_path, monkeypatch):
    _setup_env(monkeypatch)
    import importlib, config
    importlib.reload(config)

    gif_path = tmp_path / "latest.gif"
    gif_path.write_bytes(b"GIF89a")

    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()

    with patch("whatsapp.whatsapp.httpx.post", return_value=mock_response) as mock_post:
        send_gif(gif_path, caption="teste", recipient="5511999999999@s.whatsapp.net")

    payload = mock_post.call_args.kwargs["json"]
    assert payload["number"] == "5511999999999@s.whatsapp.net"


def test_send_text_posts_to_correct_endpoint(monkeypatch):
    _setup_env(monkeypatch)
    import importlib, config
    importlib.reload(config)

    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()

    with patch("whatsapp.whatsapp.httpx.post", return_value=mock_response) as mock_post:
        send_text("alerta de erro")

    call_kwargs = mock_post.call_args
    assert "sendText/test-bot" in call_kwargs.args[0]
    payload = call_kwargs.kwargs["json"]
    assert payload["text"] == "alerta de erro"
    assert payload["number"] == "group123@g.us"


def test_send_gif_raises_on_http_error(tmp_path, monkeypatch):
    _setup_env(monkeypatch)
    import importlib, config
    importlib.reload(config)

    gif_path = tmp_path / "latest.gif"
    gif_path.write_bytes(b"GIF89a")

    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "401", request=MagicMock(), response=MagicMock()
    )

    with patch("whatsapp.whatsapp.httpx.post", return_value=mock_response):
        with pytest.raises(httpx.HTTPStatusError):
            send_gif(gif_path, caption="teste")
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_whatsapp.py -v
```

Expected: `ImportError` — whatsapp.py doesn't exist yet.

- [ ] **Step 3: Create `whatsapp/whatsapp.py`**

```python
# whatsapp/whatsapp.py
import base64
from pathlib import Path

import httpx

import config


def _headers() -> dict[str, str]:
    return {"apikey": config.EVOLUTION_API_KEY, "Content-Type": "application/json"}


def send_gif(gif_path: Path, caption: str, recipient: str | None = None) -> None:
    """Send an animated GIF with caption to a WhatsApp group or number.

    Args:
        gif_path: Path to the GIF file.
        caption: Text caption sent alongside the GIF (contains the analysis).
        recipient: WhatsApp JID (group or individual). Defaults to WHATSAPP_GROUP_ID.

    Raises:
        httpx.HTTPStatusError: If Evolution API returns a non-2xx status.
    """
    to = recipient or config.WHATSAPP_GROUP_ID
    data = base64.standard_b64encode(gif_path.read_bytes()).decode("utf-8")
    payload = {
        "number": to,
        "mediatype": "image",
        "mimetype": "image/gif",
        "caption": caption,
        "media": data,
        "fileName": gif_path.name,
    }
    url = f"{config.EVOLUTION_API_URL}/message/sendMedia/{config.EVOLUTION_INSTANCE}"
    resp = httpx.post(url, json=payload, headers=_headers(), timeout=30)
    resp.raise_for_status()


def send_text(text: str, recipient: str | None = None) -> None:
    """Send a plain text message to a WhatsApp group or number.

    Args:
        text: Message body.
        recipient: WhatsApp JID. Defaults to WHATSAPP_GROUP_ID.

    Raises:
        httpx.HTTPStatusError: If Evolution API returns a non-2xx status.
    """
    to = recipient or config.WHATSAPP_GROUP_ID
    payload = {"number": to, "text": text}
    url = f"{config.EVOLUTION_API_URL}/message/sendText/{config.EVOLUTION_INSTANCE}"
    resp = httpx.post(url, json=payload, headers=_headers(), timeout=30)
    resp.raise_for_status()
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_whatsapp.py -v
```

Expected: 4 PASSED

- [ ] **Step 5: Commit**

```bash
git add whatsapp/whatsapp.py tests/test_whatsapp.py
git commit -m "feat: add whatsapp module for Evolution API delivery"
```

---

## Task 7: Scheduler / Orchestrator

**Files:**
- Create: `scheduler/scheduler.py`
- Create: `main.py`
- Create: `tests/test_scheduler.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_scheduler.py
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch, call
from PIL import Image
import pytest


def _make_images(tmp_path, count=4):
    for i in range(count):
        img = Image.new("RGB", (10, 10))
        img.save(tmp_path / f"2026-06-{9 + i:02d}.png")


def test_run_daily_job_full_success_path(tmp_path, monkeypatch):
    monkeypatch.setattr("config.STORAGE_DIR", str(tmp_path))
    _make_images(tmp_path, 4)

    with (
        patch("scheduler.scheduler.capture_map", return_value=tmp_path / "2026-06-13.png") as mock_scraper,
        patch("scheduler.scheduler.make_gif", return_value=tmp_path / "latest.gif") as mock_gif,
        patch("scheduler.scheduler.analyse", return_value="Análise ok") as mock_analyst,
        patch("scheduler.scheduler.send_gif") as mock_send_gif,
        patch("scheduler.scheduler.send_text") as mock_send_text,
    ):
        from scheduler.scheduler import run_daily_job
        run_daily_job()

    mock_scraper.assert_called_once()
    mock_gif.assert_called_once()
    mock_analyst.assert_called_once()
    mock_send_gif.assert_called_once_with(tmp_path / "latest.gif", caption="Análise ok")
    mock_send_text.assert_not_called()


def test_run_daily_job_skips_gif_when_fewer_than_4_images(tmp_path, monkeypatch):
    monkeypatch.setattr("config.STORAGE_DIR", str(tmp_path))
    _make_images(tmp_path, 2)

    with (
        patch("scheduler.scheduler.capture_map", return_value=tmp_path / "2026-06-11.png"),
        patch("scheduler.scheduler.make_gif") as mock_gif,
        patch("scheduler.scheduler.send_gif") as mock_send_gif,
    ):
        from scheduler.scheduler import run_daily_job
        run_daily_job()

    mock_gif.assert_not_called()
    mock_send_gif.assert_not_called()


def test_run_daily_job_sends_alert_on_scraper_failure(tmp_path, monkeypatch):
    monkeypatch.setattr("config.STORAGE_DIR", str(tmp_path))

    with (
        patch("scheduler.scheduler.capture_map", side_effect=Exception("Timeout 30s")),
        patch("scheduler.scheduler.send_text") as mock_send_text,
    ):
        from scheduler.scheduler import run_daily_job
        run_daily_job()

    mock_send_text.assert_called_once()
    assert "Timeout 30s" in mock_send_text.call_args.args[0]


def test_run_daily_job_sends_gif_with_fallback_text_on_analyst_failure(tmp_path, monkeypatch):
    monkeypatch.setattr("config.STORAGE_DIR", str(tmp_path))
    _make_images(tmp_path, 4)

    with (
        patch("scheduler.scheduler.capture_map", return_value=tmp_path / "2026-06-13.png"),
        patch("scheduler.scheduler.make_gif", return_value=tmp_path / "latest.gif"),
        patch("scheduler.scheduler.analyse", side_effect=Exception("API error")),
        patch("scheduler.scheduler.send_gif") as mock_send_gif,
        patch("scheduler.scheduler.send_text"),
    ):
        from scheduler.scheduler import run_daily_job
        run_daily_job()

    # Should still send GIF, with fallback caption
    mock_send_gif.assert_called_once()
    caption = mock_send_gif.call_args.kwargs["caption"]
    assert "indisponível" in caption
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_scheduler.py -v
```

Expected: `ImportError` — scheduler.py doesn't exist yet.

- [ ] **Step 3: Create `scheduler/scheduler.py`**

```python
# scheduler/scheduler.py
import logging
from datetime import date
from pathlib import Path

from apscheduler.schedulers.blocking import BlockingScheduler

import config
from analyst.analyst import analyse
from gif_maker.gif_maker import make_gif
from scraper.scraper import capture_map
from whatsapp.whatsapp import send_gif, send_text

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
log = logging.getLogger(__name__)


def run_daily_job() -> None:
    """Full daily pipeline: scrape → gif → analyse → send."""
    log.info("Daily job started")

    # 1. Capture today's map
    try:
        img_path = capture_map()
        log.info("Map captured: %s", img_path)
    except Exception as exc:
        log.error("Scraper failed: %s", exc)
        send_text(
            f"⚠️ Meteologix Bot: falha ao capturar mapa em {date.today()}. Erro: {exc}"
        )
        return

    # 2. Check accumulated image count
    storage = Path(config.STORAGE_DIR)
    png_files = sorted(storage.glob("*.png"))
    if len(png_files) < 4:
        log.info("Only %d images available — skipping GIF/analysis", len(png_files))
        return

    # 3. Build GIF
    try:
        gif_path = make_gif()
        log.info("GIF created: %s", gif_path)
    except Exception as exc:
        log.error("GIF maker failed: %s", exc)
        send_text(f"⚠️ Meteologix Bot: falha ao criar GIF. Erro: {exc}")
        return

    # 4. Generate analysis
    last_4 = sorted(storage.glob("*.png"))[-4:]
    try:
        analysis = analyse(list(last_4))
        log.info("Analysis complete")
    except Exception as exc:
        log.error("Analyst failed: %s", exc)
        analysis = (
            "⚠️ Análise automática indisponível hoje. "
            "Veja o GIF para a evolução da precipitação."
        )

    # 5. Send to WhatsApp
    try:
        send_gif(gif_path, caption=analysis)
        log.info("Message sent successfully")
    except Exception as exc:
        log.error("WhatsApp send failed: %s", exc)


def start_scheduler() -> None:
    """Start the blocking APScheduler — runs Mon–Fri at 08:00 BRT."""
    scheduler = BlockingScheduler(timezone="America/Sao_Paulo")
    scheduler.add_job(
        run_daily_job,
        "cron",
        day_of_week="mon-fri",
        hour=8,
        minute=0,
        misfire_grace_time=300,  # allow 5-minute misfire window
    )
    log.info("Scheduler started — runs Mon–Fri 08:00 BRT")
    scheduler.start()
```

- [ ] **Step 4: Create `main.py`**

```python
# main.py
from scheduler.scheduler import start_scheduler

if __name__ == "__main__":
    start_scheduler()
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
pytest tests/test_scheduler.py -v
```

Expected: 4 PASSED

- [ ] **Step 6: Run full test suite**

```bash
pytest -v
```

Expected: all tests PASSED (no failures, no errors)

- [ ] **Step 7: Commit**

```bash
git add scheduler/scheduler.py main.py tests/test_scheduler.py
git commit -m "feat: add scheduler orchestrator with error handling"
```

---

## Task 8: Docker Setup

**Files:**
- Create: `Dockerfile`
- Create: `docker-compose.yml`

- [ ] **Step 1: Create `Dockerfile`**

```dockerfile
FROM python:3.12-slim

# Install system dependencies for Playwright Chromium
RUN apt-get update && apt-get install -y \
    libnss3 libnspr4 libdbus-1-3 libatk1.0-0 libatk-bridge2.0-0 \
    libcups2 libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 \
    libxfixes3 libxrandr2 libgbm1 libasound2 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN playwright install chromium

COPY . .

CMD ["python", "main.py"]
```

- [ ] **Step 2: Create `docker-compose.yml`**

```yaml
version: "3.9"

services:
  bot:
    build: .
    restart: always
    env_file: .env
    volumes:
      - ./storage:/app/storage
    depends_on:
      - evolution-api

  evolution-api:
    image: atendai/evolution-api:latest
    restart: always
    ports:
      - "8080:8080"
    environment:
      - SERVER_URL=http://localhost:8080
      - AUTHENTICATION_TYPE=apikey
      - AUTHENTICATION_API_KEY=${EVOLUTION_API_KEY}
      - DATABASE_PROVIDER=redis
      - CACHE_REDIS_URI=redis://redis:6379
    depends_on:
      - redis

  redis:
    image: redis:7-alpine
    restart: always
    volumes:
      - redis_data:/data

volumes:
  redis_data:
```

- [ ] **Step 3: Copy `.env.example` to `.env` and fill in real values**

```bash
cp .env.example .env
# Edit .env with your real API keys and group ID
```

- [ ] **Step 4: Build and start containers**

```bash
docker-compose up -d --build
```

Expected: 3 containers start without errors (`bot`, `evolution-api`, `redis`).

- [ ] **Step 5: Scan QR Code for WhatsApp session (one-time)**

Open `http://localhost:8080` in a browser → navigate to Instances → create instance named `meteologix-bot` → scan QR Code with your WhatsApp → session persists permanently.

- [ ] **Step 6: Check bot logs**

```bash
docker-compose logs -f bot
```

Expected output contains: `Scheduler started — runs Mon–Fri 08:00 BRT`

- [ ] **Step 7: Commit**

```bash
git add Dockerfile docker-compose.yml
git commit -m "chore: add Docker and docker-compose setup"
```

---

## Task 9: Smoke Test (End-to-End Manual Trigger)

**Files:**
- Create: `scripts/run_now.py`

This script bypasses the scheduler and runs the full pipeline immediately — useful for testing with real credentials.

- [ ] **Step 1: Create `scripts/run_now.py`**

```python
# scripts/run_now.py
"""Run the full daily job immediately, bypassing the scheduler.
Use this to test the pipeline end-to-end with real credentials.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scheduler.scheduler import run_daily_job

if __name__ == "__main__":
    run_daily_job()
```

- [ ] **Step 2: Run smoke test inside the container**

```bash
docker-compose exec bot python scripts/run_now.py
```

Expected: logs show each step completing. On day 1–3, analysis and send are skipped (not enough images). On day 4+, GIF and WhatsApp message are sent.

- [ ] **Step 3: Verify map selector (if scraper fails)**

If the scraper logs a timeout or empty screenshot, the Leaflet selector may differ. To verify:
```bash
docker-compose exec bot python -c "
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    page = b.new_page(viewport={'width':1280,'height':900})
    page.goto('https://meteologix.com/br/model-charts/standard/brazil/accumulated-precipitation/20260613-0600z.html', timeout=30000)
    page.wait_for_load_state('networkidle', timeout=30000)
    print(page.content()[:3000])
    b.close()
"
```
Look for the map container class in the output and update `MAP_SELECTOR` in `scraper/scraper.py` accordingly.

- [ ] **Step 4: Commit scripts folder**

```bash
git add scripts/
git commit -m "chore: add manual trigger script for smoke testing"
```

---

## Summary

| Task | Deliverable |
|------|-------------|
| 1 | Project structure, requirements, .gitignore |
| 2 | `config.py` with validated env loading |
| 3 | `scraper/scraper.py` — Playwright map capture |
| 4 | `gif_maker/gif_maker.py` — 4-frame animated GIF |
| 5 | `analyst/analyst.py` — Claude vision analysis |
| 6 | `whatsapp/whatsapp.py` — Evolution API REST client |
| 7 | `scheduler/scheduler.py` + `main.py` — orchestrator |
| 8 | `Dockerfile` + `docker-compose.yml` |
| 9 | Smoke test + selector verification |
