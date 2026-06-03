"""Descobre o seletor correto do mapa."""
from playwright.sync_api import sync_playwright
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from scraper.scraper import build_url, _dismiss_consent_popup, USER_AGENT
from datetime import date

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context(
        viewport={"width": 1280, "height": 900},
        user_agent=USER_AGENT,
        locale="pt-BR",
        timezone_id="America/Sao_Paulo",
    )
    context.add_init_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    )
    page = context.new_page()
    page.goto(build_url(date.today()), timeout=60000)
    page.wait_for_load_state("networkidle", timeout=60000)
    page.wait_for_timeout(3000)
    _dismiss_consent_popup(page)
    page.wait_for_timeout(8000)

    # Inspeciona todos os elementos grandes e visíveis
    result = page.evaluate("""
        () => {
            const els = document.querySelectorAll('*');
            const found = [];
            for (const el of els) {
                const r = el.getBoundingClientRect();
                if (r.width > 400 && r.height > 300) {
                    found.push({
                        tag: el.tagName,
                        id: el.id,
                        cls: el.className.toString().slice(0, 80),
                        x: Math.round(r.x),
                        y: Math.round(r.y),
                        w: Math.round(r.width),
                        h: Math.round(r.height),
                    });
                }
            }
            return found.slice(0, 20);
        }
    """)

    print("Elementos grandes encontrados:")
    for r in result:
        print(f"  {r['tag']} id={r['id']!r} cls={r['cls']!r} pos=({r['x']},{r['y']}) size={r['w']}x{r['h']}")

    browser.close()
