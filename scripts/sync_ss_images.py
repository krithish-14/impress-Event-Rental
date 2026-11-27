"""Copy Signature Seating product cutouts into static with URL-safe names."""
from __future__ import annotations

import re
from pathlib import Path

from PIL import Image

BASE = Path(__file__).resolve().parents[1]
SRC_ROOT = BASE / "templates" / "images" / "signature seating"
DST_ROOT = BASE / "static" / "images" / "signature-seating" / "products"
# Prefer the first existing source folder alias for each destination.
FOLDER_ALIASES = (
    (("Chair", "Chairs"), "chairs"),
    (("Diwan",), "diwan"),
    (("Sofa",), "sofa"),
)
SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
PAD_RATIO = 0.02
MAX_SIDE = 1600


def slugify(value: str) -> str:
    value = value.casefold()
    value = re.sub(r"[^\w\s-]", "", value, flags=re.UNICODE)
    value = re.sub(r"[-\s]+", "-", value).strip("-")
    return value


def clean_stem(stem: str) -> str:
    text = re.sub(r"\s+", " ", stem).strip()
    text = re.sub(r"\s*-\s*Copy$", "", text, flags=re.I).strip()
    text = re.sub(r"\(([^)]+)\)", r" (\1)", text)
    return re.sub(r"\s+", " ", text).strip()


def trim_cutout(src: Path, dest: Path) -> None:
    """Crop transparent padding and keep natural aspect so cards fill cleanly."""
    im = Image.open(src).convert("RGBA")
    bbox = im.getbbox()
    if not bbox:
        im.save(dest, optimize=True)
        return
    cropped = im.crop(bbox)
    cw, ch = cropped.size
    pad_x = max(4, int(cw * PAD_RATIO))
    pad_y = max(4, int(ch * PAD_RATIO))
    out = Image.new("RGBA", (cw + pad_x * 2, ch + pad_y * 2), (0, 0, 0, 0))
    out.paste(cropped, (pad_x, pad_y), cropped)
    width, height = out.size
    scale = min(1.0, MAX_SIDE / max(width, height))
    if scale < 1:
        out = out.resize(
            (max(1, int(width * scale)), max(1, int(height * scale))),
            Image.Resampling.LANCZOS,
        )
    out.save(dest, optimize=True)


def resolve_source(aliases: tuple[str, ...]) -> Path | None:
    for name in aliases:
        path = SRC_ROOT / name
        if path.is_dir():
            return path
    return None


def main() -> None:
    copied = 0
    for aliases, dest_name in FOLDER_ALIASES:
        src = resolve_source(aliases)
        dst = DST_ROOT / dest_name
        dst.mkdir(parents=True, exist_ok=True)
        for old in dst.iterdir():
            if old.is_file():
                old.unlink()
        if src is None:
            print(f"{dest_name}: source folder missing ({', '.join(aliases)})")
            continue

        files = [
            path
            for path in sorted(src.iterdir())
            if path.is_file() and path.suffix.lower() in SUFFIXES
        ]
        base_stems = {
            clean_stem(re.sub(r"\s*-\s*Copy$", "", path.stem, flags=re.I))
            for path in files
            if not re.search(r"-\s*Copy$", path.stem, re.I)
        }
        used: set[str] = set()
        for path in files:
            is_copy = bool(re.search(r"-\s*Copy$", path.stem, re.I))
            name = clean_stem(path.stem)
            # Keep "- Copy" only when no original of the same product exists.
            if is_copy and name in base_stems:
                continue
            slug = slugify(name) or "item"
            if slug in used:
                slug = f"{slug}-{len(used) + 1}"
            used.add(slug)
            dest = dst / f"{slug}{path.suffix.lower()}"
            if path.suffix.lower() == ".png":
                trim_cutout(path, dest)
            else:
                dest.write_bytes(path.read_bytes())
            copied += 1
            print(f"{dest_name}: {name} -> {dest.name} {Image.open(dest).size}")
    print(f"TOTAL {copied}")


if __name__ == "__main__":
    main()
