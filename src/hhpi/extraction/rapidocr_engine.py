from __future__ import annotations

from pathlib import Path

from hhpi.layout.models import BBox
from .contracts import OCRPage, OCRToken
from .preprocess import PreprocessOptions, preprocess_for_ocr


class RapidOCREngine:
    """Optional ONNX/OpenVINO deployment path for Paddle-derived OCR models.

    For Persian, pass an Arabic-family PP-OCRv5 recognition model and its matching character dictionary.
    This keeps production inference free/offline while avoiding the full Paddle runtime.
    """

    name = "rapidocr"

    def __init__(
        self,
        *,
        rec_model_path: str | None = None,
        rec_keys_path: str | None = None,
    ) -> None:
        try:
            from rapidocr import RapidOCR  # type: ignore
        except ImportError as exc:
            raise RuntimeError("Install optional dependency group 'ocr-rapidocr'") from exc
        kwargs = {}
        if rec_model_path:
            kwargs["Rec.model_path"] = rec_model_path
        if rec_keys_path:
            kwargs["Rec.rec_keys_path"] = rec_keys_path
        self.engine = RapidOCR(params=kwargs or None)
        self.preprocess = PreprocessOptions(scale=2.0, clahe=True)

    def extract(self, image_path: str | Path, *, region: BBox | None = None) -> OCRPage:
        import numpy as np

        image, (ox, oy), scale = preprocess_for_ocr(image_path, region=region, options=self.preprocess)
        result = self.engine(np.asarray(image))
        txts = getattr(result, "txts", None) or []
        scores = getattr(result, "scores", None) or []
        boxes = getattr(result, "boxes", None) or []
        tokens: list[OCRToken] = []
        for text, confidence, quad in zip(txts, scores, boxes):
            xs = [p[0] for p in quad]
            ys = [p[1] for p in quad]
            tokens.append(
                OCRToken(
                    text=str(text),
                    confidence=float(confidence),
                    bbox=BBox(
                        int(min(xs) / scale + ox), int(min(ys) / scale + oy),
                        int(max(xs) / scale + ox), int(max(ys) / scale + oy),
                    ),
                )
            )
        return OCRPage(
            engine=self.name,
            image_path=str(image_path),
            tokens=tuple(tokens),
            raw_text=" ".join(t.text for t in tokens),
            metadata={"region": region.as_tuple() if region else None},
        )
