from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

from hhpi.layout.models import BBox


@dataclass(frozen=True)
class OCRToken:
    text: str
    confidence: float
    bbox: BBox


@dataclass(frozen=True)
class OCRPage:
    engine: str
    image_path: str
    tokens: tuple[OCRToken, ...] = ()
    raw_text: str | None = None
    metadata: dict = field(default_factory=dict)

    @property
    def mean_confidence(self) -> float:
        if not self.tokens:
            return 0.0
        return round(sum(t.confidence for t in self.tokens) / len(self.tokens), 4)


class OCREngine(Protocol):
    name: str

    def extract(self, image_path: str | Path, *, region: BBox | None = None) -> OCRPage:
        ...


@dataclass(frozen=True)
class EngineCapability:
    name: str
    supports_persian: bool
    supports_tables: bool
    supports_bboxes: bool
    local: bool
    enabled: bool = False
    notes: str = ""


ENGINE_REGISTRY: tuple[EngineCapability, ...] = (
    EngineCapability("paddleocr", True, True, True, True, enabled=True, notes="primary OSS candidate; PP-OCRv5 Arabic-family model includes Persian + English"),
    EngineCapability("rapidocr", True, False, True, True, enabled=True, notes="lightweight OSS ONNX deployment path for Paddle-derived models"),
    EngineCapability("easyocr", True, False, True, True, enabled=True, notes="secondary OSS recognizer; supports fa+en"),
    EngineCapability("tesseract", True, False, True, True, enabled=True, notes="Apache-2.0 local fallback; strongest after supplier/brand crop + upscale"),
)
