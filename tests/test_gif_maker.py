from pathlib import Path
from unittest.mock import patch, MagicMock
from PIL import Image
import pytest

from gif_maker.gif_maker import get_label, make_gif


def test_get_label_formats_weekday_and_date():
    assert get_label("2026-06-13.png") == "Sáb 13/06"


def test_get_label_monday():
    assert get_label("2026-06-08.png") == "Seg 08/06"


def test_get_label_returns_empty_for_invalid():
    assert get_label("nodate.png") == ""


def test_make_gif_creates_file(tmp_path):
    mock_config = MagicMock()
    mock_config.STORAGE_DIR = str(tmp_path)
    dates = ["2026-06-09", "2026-06-10", "2026-06-11", "2026-06-12"]
    for d in dates:
        img = Image.new("RGB", (100, 80), color=(100, 150, 200))
        img.save(tmp_path / f"{d}.png")
    output = tmp_path / "test_output.gif"
    with patch("gif_maker.gif_maker.config", mock_config):
        result = make_gif(output_path=output)
    assert result == output
    assert output.exists()


def test_make_gif_raises_when_fewer_than_4_images(tmp_path):
    mock_config = MagicMock()
    mock_config.STORAGE_DIR = str(tmp_path)
    img = Image.new("RGB", (100, 80), color=(100, 150, 200))
    img.save(tmp_path / "2026-06-09.png")
    with patch("gif_maker.gif_maker.config", mock_config):
        with pytest.raises(ValueError, match="Need 4 images"):
            make_gif()


def test_make_gif_uses_last_4_when_more_available(tmp_path):
    mock_config = MagicMock()
    mock_config.STORAGE_DIR = str(tmp_path)
    dates = ["2026-06-07", "2026-06-08", "2026-06-09", "2026-06-10", "2026-06-11"]
    for d in dates:
        img = Image.new("RGB", (100, 80), color=(100, 150, 200))
        img.save(tmp_path / f"{d}.png")
    output = tmp_path / "test_output.gif"
    with patch("gif_maker.gif_maker.config", mock_config):
        result = make_gif(output_path=output)
    assert result.exists()
