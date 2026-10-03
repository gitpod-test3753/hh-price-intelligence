from __future__ import annotations

from dataclasses import dataclass
import importlib.util
import shutil


@dataclass(frozen=True)
class OSSAvailability:
    engine: str
    available: bool
    reason: str


def discover_oss_engines() -> tuple[OSSAvailability, ...]:
    return (
        OSSAvailability(
            "tesseract",
            shutil.which("tesseract") is not None and importlib.util.find_spec("pytesseract") is not None,
            "system binary + pytesseract",
        ),
        OSSAvailability(
            "paddleocr",
            importlib.util.find_spec("paddleocr") is not None,
            "PP-OCRv5; install compatible PaddlePaddle runtime",
        ),
        OSSAvailability(
            "rapidocr",
            importlib.util.find_spec("rapidocr") is not None,
            "ONNX/OpenVINO deployment of Paddle-derived models",
        ),
        OSSAvailability(
            "easyocr",
            importlib.util.find_spec("easyocr") is not None,
            "PyTorch; supports fa+en",
        ),
    )
