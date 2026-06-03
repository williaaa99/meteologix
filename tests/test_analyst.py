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
    decoded = base64.standard_b64decode(result)
    assert len(decoded) > 0


def test_analyse_calls_claude_with_4_image_blocks(tmp_path, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

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
