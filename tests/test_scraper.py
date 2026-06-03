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


def test_capture_map_saves_file(tmp_path):
    mock_config = MagicMock()
    mock_config.STORAGE_DIR = str(tmp_path)
    mock_element = MagicMock()
    mock_page = MagicMock()
    mock_page.wait_for_selector.return_value = mock_element
    mock_browser = MagicMock()
    mock_browser.new_page.return_value = mock_page
    mock_playwright_ctx = MagicMock()
    mock_playwright_ctx.__enter__ = MagicMock(return_value=mock_playwright_ctx)
    mock_playwright_ctx.__exit__ = MagicMock(return_value=False)
    mock_playwright_ctx.chromium.launch.return_value = mock_browser
    with patch("scraper.scraper.config", mock_config):
        with patch("scraper.scraper.sync_playwright", return_value=mock_playwright_ctx):
            result = capture_map(date(2026, 6, 13))
    assert result == tmp_path / "2026-06-13.png"
    mock_element.screenshot.assert_called_once_with(path=str(tmp_path / "2026-06-13.png"))
    mock_browser.close.assert_called_once()


def test_capture_map_raises_on_timeout(tmp_path):
    mock_config = MagicMock()
    mock_config.STORAGE_DIR = str(tmp_path)
    mock_page = MagicMock()
    mock_page.wait_for_selector.side_effect = Exception("Timeout")
    mock_browser = MagicMock()
    mock_browser.new_page.return_value = mock_page
    mock_playwright_ctx = MagicMock()
    mock_playwright_ctx.__enter__ = MagicMock(return_value=mock_playwright_ctx)
    mock_playwright_ctx.__exit__ = MagicMock(return_value=False)
    mock_playwright_ctx.chromium.launch.return_value = mock_browser
    with patch("scraper.scraper.config", mock_config):
        with patch("scraper.scraper.sync_playwright", return_value=mock_playwright_ctx):
            with pytest.raises(Exception, match="Timeout"):
                capture_map(date(2026, 6, 13))
    mock_browser.close.assert_called_once()
