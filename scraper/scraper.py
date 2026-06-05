from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import config

TIMEOUT_S = 180
CHROMIUM_PATH = "/usr/bin/chromium-browser"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)


def build_url(target_date: date) -> str:
    """Return the Meteologix 15-day accumulated precipitation URL."""
    forecast_date = target_date + timedelta(days=15)
    return (
        "https://meteologix.com/br/model-charts/standard/brazil/"
        f"accumulated-precipitation/{forecast_date.strftime('%Y%m%d')}-1200z.html"
    )


def _make_driver() -> webdriver.Chrome:
    """Create a headless Chrome driver using the system Chromium."""
    options = Options()
    options.binary_location = CHROMIUM_PATH
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-setuid-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--window-size=1600,1200")
    options.add_argument(f"--user-agent={USER_AGENT}")
    options.add_argument("--lang=pt-BR")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    service = Service()
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_page_load_timeout(180)
    driver.set_script_timeout(180)
    driver.execute_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    )
    return driver


def _dismiss_consent_popup(driver: webdriver.Chrome) -> None:
    """Click Accept inside the consent iframe if present."""
    try:
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        for iframe in iframes:
            src = iframe.get_attribute("src") or ""
            if "data-c" in src and "meteologix" in src:
                driver.switch_to.frame(iframe)
                try:
                    btn = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable(
                            (By.XPATH, "//button[contains(text(),'Accept')]")
                        )
                    )
                    btn.click()
                    import time
                    time.sleep(2)
                except Exception:
                    pass
                finally:
                    driver.switch_to.default_content()
                return
    except Exception:
        pass


def capture_map(target_date: date | None = None) -> Path:
    """Launch headless Chromium, screenshot the map, save to storage.

    Args:
        target_date: Date to capture. Defaults to today.

    Returns:
        Path to the saved PNG file.

    Raises:
        Exception: If map element does not load within timeout.
    """
    if target_date is None:
        target_date = date.today()

    url = build_url(target_date)
    output_path = Path(config.STORAGE_DIR) / f"{target_date.isoformat()}.png"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    driver = _make_driver()
    try:
        driver.get(url)

        # Wait for page to load
        import time
        time.sleep(10)

        _dismiss_consent_popup(driver)

        # Wait for map image to appear
        time.sleep(15)

        # Screenshot the map image element
        map_el = WebDriverWait(driver, TIMEOUT_S).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#main-image-content img"))
        )
        map_el.screenshot(str(output_path))

    finally:
        driver.quit()

    return output_path
