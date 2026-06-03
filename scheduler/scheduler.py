from __future__ import annotations

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
    """Full daily pipeline: scrape -> gif -> analyse -> send."""
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
    """Start the blocking APScheduler — runs Mon-Fri at 08:00 BRT."""
    scheduler = BlockingScheduler(timezone="America/Sao_Paulo")
    scheduler.add_job(
        run_daily_job,
        "cron",
        day_of_week="mon-fri",
        hour=8,
        minute=0,
        misfire_grace_time=300,
    )
    log.info("Scheduler started — runs Mon-Fri 08:00 BRT")
    scheduler.start()
