from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)  # headless agora
    page = b.new_page(viewport={"width": 1280, "height": 900})
    page.goto(
        "https://meteologix.com/br/model-charts/standard/brazil/accumulated-precipitation/20260601-0600z.html",
        timeout=60000,
    )
    page.wait_for_load_state("networkidle", timeout=60000)
    page.wait_for_timeout(3000)

    # Fecha popup
    for frame in page.frames:
        if "data-c" in frame.url and "meteologix.com" in frame.url:
            try:
                btn = frame.wait_for_selector("button:has-text('Accept')", timeout=5000)
                btn.click()
                print("Popup fechado")
                page.wait_for_timeout(2000)
            except Exception as e:
                print(f"Erro popup: {e}")

    page.wait_for_timeout(5000)

    # Procura todos os elementos com 'leaflet' no nome de classe
    result = page.evaluate("""
        () => {
            const all = document.querySelectorAll('[class*="leaflet"]');
            return Array.from(all).slice(0, 10).map(el => ({
                tag: el.tagName,
                classes: el.className,
                visible: el.offsetWidth > 0 && el.offsetHeight > 0
            }));
        }
    """)
    print("Elementos leaflet encontrados:", len(result))
    for r in result:
        print(f"  {r['tag']} | classes: {r['classes'][:60]} | visivel: {r['visible']}")

    page.screenshot(path="debug2.png")
    print("Screenshot salvo em debug2.png")
    b.close()
