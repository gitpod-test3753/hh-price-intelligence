from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from PIL import Image


def describe_fixture(path: Path) -> dict:
    data = path.read_bytes()
    with Image.open(path) as im:
        width, height = im.size
    return {
        "file": path.name,
        "sha256": sha256(data).hexdigest(),
        "width": width,
        "height": height,
        "bytes": len(data),
    }


def build_manifest(folder: Path) -> list[dict]:
    return [describe_fixture(p) for p in sorted(folder.glob("*.jpg"))]
