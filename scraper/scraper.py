from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

import config

TIMEOUT_MS = 60_000

# Realistic browser fingerprint to avoid bot detection
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)


def build_url(target_date: date) -> str:
    """Return the Meteologix 15-day accumulated precipitation URL.

    The URL uses today + 15 days with 1200z to show the full 15-day forecast.
    """
    forecast_date = target_date + timedelta(days=15)
    return (
        "https://meteologix.com/br/model-charts/standard/brazil/"
        f"accumulated-precipitation/{forecast_date.strftime('%Y%m%d')}-1200z.html"
    )


def _dismiss_consent_popup(page) -> None:
    """Click Accept inside the consent iframe if present."""
    for frame in page.frames:
        if "data-c" in frame.url and "meteologix.com" in frame.url:
            try:
                btn = frame.wait_for_selector("button:has-text('Accept')", timeout=5000)
                btn.click()
                page.wait_for_timeout(2000)
            except Exception:
                pass
            return


def capture_map(target_date: date | None = None) -> Path:
    """Launch Chromium, screenshot the map area, save to storage.

    Args:
        target_date: Date to capture. Defaults to today.

    Returns:
        Path to the saved PNG file.

    Raises:
        Exception: If page does not load within TIMEOUT_MS.
    """
    if target_date is None:
        target_date = date.today()

    url = build_url(target_date)
    output_path = Path(config.STORAGE_DIR) / f"{target_date.isoformat()}.png"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-setuid-sandbox",
            ],
        )
        try:
            context = browser.new_context(
                viewport={"width": 1280, "height": 900},
                user_agent=USER_AGENT,
                locale="pt-BR",
                timezone_id="America/Sao_Paulo",
                extra_http_headers={
                    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
                },
            )
            context.add_init_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            )
            page = context.new_page()
            page.goto(url, timeout=TIMEOUT_MS)
            page.wait_for_load_state("networkidle", timeout=TIMEOUT_MS)
            page.wait_for_timeout(3000)

            _dismiss_consent_popup(page)

            # Wait for map to fully render after popup close
            page.wait_for_timeout(8000)

            # Screenshot the map image element directly
            map_element = page.wait_for_selector("#main-image-content img", timeout=TIMEOUT_MS)
            map_element.screenshot(path=str(output_path))

        finally:
            browser.close()

    return output_path
