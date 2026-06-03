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

    mock_send_gif.assert_called_once()
    caption = mock_send_gif.call_args.kwargs["caption"]
    assert "indisponível" in caption
