"""Normalize uploaded catalogue photos to a fixed square canvas."""
from __future__ import annotations

from io import BytesIO
from pathlib import Path

from django.core.files.base import ContentFile
from PIL import Image, ImageOps

TARGET_SIZE = 1200
OUTPUT_FORMAT = "JPEG"
OUTPUT_QUALITY = 90


def _needs_normalize(image_field) -> bool:
    if not image_field:
        return False
    # Fresh uploads are uncommitted; already-saved files are committed.
    return not getattr(image_field, "_committed", True)


def normalize_to_square(image_field, basename: str = "photo") -> bool:
    """
    Fit any uploaded image into a 1200×1200 white square (no crop).
    Returns True when the field was rewritten.
    """
    if not _needs_normalize(image_field):
        return False

    image_field.open()
    with Image.open(image_field) as raw:
        img = ImageOps.exif_transpose(raw)
        if img.mode not in {"RGB", "RGBA"}:
            img = img.convert("RGBA")
        elif img.mode == "RGB":
            img = img.convert("RGBA")

        img.thumbnail((TARGET_SIZE, TARGET_SIZE), Image.Resampling.LANCZOS)
        canvas = Image.new("RGBA", (TARGET_SIZE, TARGET_SIZE), (255, 255, 255, 255))
        offset = (
            (TARGET_SIZE - img.width) // 2,
            (TARGET_SIZE - img.height) // 2,
        )
        canvas.paste(img, offset, img)
        final = canvas.convert("RGB")

        buffer = BytesIO()
        final.save(buffer, format=OUTPUT_FORMAT, quality=OUTPUT_QUALITY, optimize=True)
        buffer.seek(0)

    stem = Path(getattr(image_field, "name", "") or basename).stem or basename
    safe_stem = "".join(ch if ch.isalnum() or ch in "-_" else "-" for ch in stem).strip("-") or basename
    filename = f"{safe_stem}-{TARGET_SIZE}.jpg"
    image_field.save(filename, ContentFile(buffer.read()), save=False)
    return True
