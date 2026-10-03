import shutil
from pathlib import Path

import pytest
from PIL import Image, ImageDraw, ImageFont

pytest.importorskip("pytesseract")
from hhpi.extraction.tesseract_engine import TesseractEngine


@pytest.mark.skipif(shutil.which("tesseract") is None, reason="tesseract binary not installed")
def test_tesseract_reads_synthetic_price_line(tmp_path: Path):
    path = tmp_path / "line.png"
    im = Image.new("RGB", (900, 120), "white")
    draw = ImageDraw.Draw(im)
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    font = ImageFont.truetype(font_path, 44) if Path(font_path).exists() else None
    draw.text((20, 25), "Note 15 8/256 Black 80500", fill="black", font=font)
    im.save(path)

    engine = TesseractEngine(languages="eng", psm=7)
    page = engine.extract(path)
    compact = (page.raw_text or "").replace(" ", "")
    assert "Note15" in compact
    assert "80500" in compact
