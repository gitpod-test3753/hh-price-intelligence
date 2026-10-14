from __future__ import annotations

from functools import lru_cache
import os
from pathlib import Path
import shutil

import pytesseract
from pytesseract import Output

from hhpi.layout.models import BBox
from .contracts import OCRPage, OCRToken
from .preprocess import PreprocessOptions, preprocess_for_ocr

# Prevent OpenMP thread spinning inside Tesseract 5 on small cell crops (4x-8x faster per call).
os.environ.setdefault("OMP_THREAD_LIMIT", "1")


@lru_cache(maxsize=1)
def _cached_installed_languages() -> tuple[str, ...]:
    try:
        return tuple(sorted(str(x) for x in pytesseract.get_languages(config="")))
    except Exception:
        return ()


@lru_cache(maxsize=1)
def _cached_tesseract_version() -> str:
    try:
        return str(pytesseract.get_tesseract_version())
    except Exception:
        return "unknown"


class TesseractEngine:
    """Local Apache-2.0 OCR baseline/fallback for Persian + English."""

    name = "tesseract"

    def __init__(
        self,
        *,
        languages: str = "fas+eng",
        psm: int = 6,
        oem: int = 1,
        preprocess: PreprocessOptions | None = None,
        extra_config: str = "",
    ) -> None:
        self.languages = languages
        self.psm = psm
        self.oem = oem
        self.preprocess = preprocess or PreprocessOptions(scale=3.0, clahe=True)
        self.extra_config = extra_config.strip()

    @staticmethod
    def is_available() -> bool:
        return shutil.which("tesseract") is not None

    def installed_languages(self) -> tuple[str, ...]:
        return _cached_installed_languages()

    def extract(self, image_path: str | Path, *, region: BBox | None = None) -> OCRPage:
        if not self.is_available():
            raise RuntimeError("Tesseract binary is not installed")
        installed = self.installed_languages()
        missing = [lang for lang in self.languages.split("+") if lang not in installed]
        if missing:
            raise RuntimeError(f"Missing Tesseract language data: {', '.join(missing)}")

        image, (ox, oy), scale = preprocess_for_ocr(
            image_path, region=region, options=self.preprocess
        )
        config = f"--oem {self.oem} --psm {self.psm} -c preserve_interword_spaces=1"
        if self.extra_config:
            config = f"{config} {self.extra_config}"
        data = pytesseract.image_to_data(
            image, lang=self.languages, config=config, output_type=Output.DICT
        )

        tokens: list[OCRToken] = []
        raw_parts: list[str] = []
        pad_offset = float(self.preprocess.pad_px) if self.preprocess.pad_px > 0 else 0.0
        pad_offset_x = float(self.preprocess.pad_px + 4) if self.preprocess.pad_px > 0 else 0.0
        for i, text in enumerate(data.get("text", [])):
            text = (text or "").strip()
            if not text:
                continue
            try:
                conf_raw = float(data["conf"][i])
            except (TypeError, ValueError, KeyError):
                conf_raw = -1.0
            confidence = max(0.0, min(1.0, conf_raw / 100.0))
            left = max(0.0, float(data["left"][i]) - pad_offset_x) / scale + ox
            top = max(0.0, float(data["top"][i]) - pad_offset) / scale + oy
            width = float(data["width"][i]) / scale
            height = float(data["height"][i]) / scale
            tokens.append(
                OCRToken(
                    text=text,
                    confidence=confidence,
                    bbox=BBox(int(left), int(top), int(left + width), int(top + height)),
                )
            )
            raw_parts.append(text)

        return OCRPage(
            engine=self.name,
            image_path=str(image_path),
            tokens=tuple(tokens),
            raw_text=" ".join(raw_parts),
            metadata={
                "languages": self.languages,
                "psm": self.psm,
                "oem": self.oem,
                "preprocess": self.preprocess.__dict__,
                "tesseract_version": _cached_tesseract_version(),
                "region": region.as_tuple() if region else None,
                "extra_config": self.extra_config,
            },
        )
