from __future__ import annotations

from pathlib import Path

from hhpi.layout.models import BBox
from .contracts import OCRPage, OCRToken
from .preprocess import PreprocessOptions, preprocess_for_ocr


class EasyOCREngine:
    """Optional local Apache-2.0 challenger. Supports Persian via lang=['fa','en']."""

    name = "easyocr"

    def __init__(self, *, gpu: bool = False, languages: tuple[str, ...] = ("fa", "en")) -> None:
        try:
            import easyocr  # type: ignore
        except ImportError as exc:
            raise RuntimeError("Install optional dependency group 'ocr-easyocr'") from exc
        self.languages = languages
        self.reader = easyocr.Reader(list(languages), gpu=gpu)
        self.preprocess = PreprocessOptions(scale=2.0, clahe=True)

    def extract(self, image_path: str | Path, *, region: BBox | None = None) -> OCRPage:
        image, (ox, oy), scale = preprocess_for_ocr(image_path, region=region, options=self.preprocess)
        results = self.reader.readtext(image, detail=1, paragraph=False)
        tokens: list[OCRToken] = []
        for quad, text, confidence in results:
            xs = [p[0] for p in quad]
            ys = [p[1] for p in quad]
            x1, x2 = min(xs) / scale + ox, max(xs) / scale + ox
            y1, y2 = min(ys) / scale + oy, max(ys) / scale + oy
            tokens.append(
                OCRToken(
                    text=str(text),
                    confidence=float(confidence),
                    bbox=BBox(int(x1), int(y1), int(x2), int(y2)),
                )
            )
        return OCRPage(
            engine=self.name,
            image_path=str(image_path),
            tokens=tuple(tokens),
            raw_text=" ".join(t.text for t in tokens),
            metadata={"languages": self.languages, "region": region.as_tuple() if region else None},
        )
