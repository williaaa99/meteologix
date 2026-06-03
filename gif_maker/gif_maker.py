from __future__ import annotations
import re
from datetime import date
from pathlib import Path

from PIL import Image, ImageDraw

import config

WEEKDAY_PT = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
FRAME_DURATION_MS = 1500


def get_label(filename: str) -> str:
    """Extract date from a 'YYYY-MM-DD.png' filename and return 'Seg DD/MM'."""
    match = re.search(r"(\d{4}-\d{2}-\d{2})", filename)
    if not match:
        return ""
    d = date.fromisoformat(match.group(1))
    return f"{WEEKDAY_PT[d.weekday()]} {d.day:02d}/{d.month:02d}"


def _overlay_label(img: Image.Image, label: str) -> Image.Image:
    """Draw a white label with black shadow in the bottom-left corner."""
    draw = ImageDraw.Draw(img)
    x, y = 10, img.height - 30
    draw.text((x + 1, y + 1), label, fill="black")  # shadow
    draw.text((x, y), label, fill="white")
    return img


def make_gif(output_path: Path | None = None) -> Path:
    """Compose the last 4 saved PNGs into an animated GIF.

    Args:
        output_path: Destination path for the GIF. Defaults to storage/latest.gif.

    Returns:
        Path to the generated GIF.

    Raises:
        ValueError: If fewer than 4 PNG images are found in storage.
    """
    storage = Path(config.STORAGE_DIR)
    images = sorted(storage.glob("*.png"))[-4:]

    if len(images) < 4:
        raise ValueError(f"Need 4 images, found {len(images)}")

    if output_path is None:
        output_path = storage / "latest.gif"

    frames: list[Image.Image] = []
    for img_path in images:
        with Image.open(img_path) as raw:
            img = raw.convert("RGB")  # convert creates a new in-memory image; file handle released here
        label = get_label(img_path.name)
        if label:
            img = _overlay_label(img, label)
        frames.append(img)

    frames[0].save(
        output_path,
        save_all=True,
        append_images=frames[1:],
        duration=FRAME_DURATION_MS,
        loop=0,
        format="GIF",
    )
    return output_path
