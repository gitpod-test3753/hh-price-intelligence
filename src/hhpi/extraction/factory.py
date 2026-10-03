from __future__ import annotations

import os
from typing import Any

from .easyocr_engine import EasyOCREngine
from .oss_registry import discover_oss_engines
from .paddle_engine import PaddleOCREngine
from .rapidocr_engine import RapidOCREngine
from .tesseract_engine import TesseractEngine


DEFAULT_OSS_ORDER = ("paddleocr", "rapidocr", "easyocr", "tesseract")


def available_oss_engine_names() -> tuple[str, ...]:
    availability = {item.engine: item.available for item in discover_oss_engines()}
    return tuple(name for name in DEFAULT_OSS_ORDER if availability.get(name, False))


def build_oss_engine(name: str | None = None, **kwargs: Any):
    """Build a local/free OCR engine.

    This factory intentionally has no cloud/paid provider branches. If no name is supplied it chooses the
    first locally available engine in DEFAULT_OSS_ORDER. Set HHPI_OCR_ENGINE to pin one in deployment.
    """
    selected = (name or os.getenv("HHPI_OCR_ENGINE") or "").strip().lower()
    if not selected:
        available = available_oss_engine_names()
        if not available:
            raise RuntimeError("No local OSS OCR engine is available")
        selected = available[0]

    if selected == "paddleocr":
        return PaddleOCREngine(**kwargs)
    if selected == "rapidocr":
        return RapidOCREngine(**kwargs)
    if selected == "easyocr":
        return EasyOCREngine(**kwargs)
    if selected == "tesseract":
        return TesseractEngine(**kwargs)
    raise ValueError(f"Unknown OSS OCR engine: {selected}")
