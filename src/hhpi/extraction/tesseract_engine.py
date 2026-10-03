from __future__ import annotations

import shutil
from pathlib import Path

import pytesseract
from pytesseract import Output

from hhpi.layout.models import BBox
from .contracts import OCRPage, OCRToken
from .preprocess import PreprocessOptions, preprocess_for_ocr


class TesseractEngine:
    """Local Apache-2.0 OCR baseline/fallback for Persian + English.

    Dense competitor sheets are deliberately cropped/upscaled before recognition. Full-page Tesseract
    on multi-column price lists is materially worse than supplier/brand-region OCR.
    """

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
        try:
            return tuple(sorted(str(x) for x in pytesseract.get_languages(config="")))
        except Exception:
            return ()

    def extract(self, image_path: str | Path, *, region: BBox | None = None) -> OCRPage:
        if not self.is_available():
            raise RuntimeError("Tesseract binary is not installed")
        missing = [lang for lang in self.languages.split("+") if lang not in self.installed_languages()]
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
        for i, text in enumerate(data.get("text", [])):
            text = (text or "").strip()
            if not text:
                continue
            try:
                conf_raw = float(data["conf"][i])
            except (TypeError, ValueError, KeyError):
                conf_raw = -1.0
            confidence = max(0.0, min(1.0, conf_raw / 100.0))
            left = float(data["left"][i]) / scale + ox
            top = float(data["top"][i]) / scale + oy
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
                "tesseract_version": str(pytesseract.get_tesseract_version()),
                "region": region.as_tuple() if region else None,
                "extra_config": self.extra_config,
            },
        )
