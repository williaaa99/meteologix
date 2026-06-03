from pathlib import Path
from unittest.mock import MagicMock, patch
import httpx
import pytest

from whatsapp.whatsapp import send_gif, send_text


def _mock_config():
    cfg = MagicMock()
    cfg.EVOLUTION_API_KEY = "evo-test"
    cfg.EVOLUTION_API_URL = "http://localhost:8080"
    cfg.EVOLUTION_INSTANCE = "test-bot"
    cfg.WHATSAPP_GROUP_ID = "group123@g.us"
    return cfg


def test_send_gif_posts_to_correct_endpoint(tmp_path):
    gif_path = tmp_path / "latest.gif"
    gif_path.write_bytes(b"GIF89a")

    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()

    with patch("whatsapp.whatsapp.config", _mock_config()):
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


def test_send_gif_accepts_custom_recipient(tmp_path):
    gif_path = tmp_path / "latest.gif"
    gif_path.write_bytes(b"GIF89a")

    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()

    with patch("whatsapp.whatsapp.config", _mock_config()):
        with patch("whatsapp.whatsapp.httpx.post", return_value=mock_response) as mock_post:
            send_gif(gif_path, caption="teste", recipient="5511999999999@s.whatsapp.net")

    payload = mock_post.call_args.kwargs["json"]
    assert payload["number"] == "5511999999999@s.whatsapp.net"


def test_send_text_posts_to_correct_endpoint():
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()

    with patch("whatsapp.whatsapp.config", _mock_config()):
        with patch("whatsapp.whatsapp.httpx.post", return_value=mock_response) as mock_post:
            send_text("alerta de erro")

    call_kwargs = mock_post.call_args
    assert "sendText/test-bot" in call_kwargs.args[0]
    payload = call_kwargs.kwargs["json"]
    assert payload["text"] == "alerta de erro"
    assert payload["number"] == "group123@g.us"


def test_send_gif_raises_on_http_error(tmp_path):
    gif_path = tmp_path / "latest.gif"
    gif_path.write_bytes(b"GIF89a")

    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "401", request=MagicMock(), response=MagicMock()
    )

    with patch("whatsapp.whatsapp.config", _mock_config()):
        with patch("whatsapp.whatsapp.httpx.post", return_value=mock_response):
            with pytest.raises(httpx.HTTPStatusError):
                send_gif(gif_path, caption="teste")
