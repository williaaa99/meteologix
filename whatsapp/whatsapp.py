from __future__ import annotations

import subprocess
from pathlib import Path

import config

# Caminho do script Node.js de envio
SEND_SCRIPT = Path(__file__).parent / "send.js"


def _run_node(args: list[str]) -> None:
    """Run the Node.js send script with the given arguments."""
    cmd = ["node", str(SEND_SCRIPT)] + args
    result = subprocess.run(cmd, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"send.js falhou com código {result.returncode}")


def send_gif(gif_path: Path, caption: str, recipient: str | None = None) -> None:
    """Send an animated GIF with caption to the WhatsApp group.

    Args:
        gif_path: Path to the GIF file.
        caption: Text caption sent alongside the GIF.
        recipient: Ignored — group name is set in send.js config.

    Raises:
        RuntimeError: If the Node.js script fails.
    """
    _run_node(["--text", caption, "--gif", str(gif_path)])


def send_text(text: str, recipient: str | None = None) -> None:
    """Send a plain text message to the WhatsApp group.

    Args:
        text: Message body.
        recipient: Ignored — group name is set in send.js config.

    Raises:
        RuntimeError: If the Node.js script fails.
    """
    _run_node(["--text", text])
