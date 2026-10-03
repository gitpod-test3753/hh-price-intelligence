from __future__ import annotations

from pathlib import Path

from hhpi.layout.models import BBox
from .contracts import OCRPage, OCRToken
from .preprocess import PreprocessOptions, preprocess_for_ocr


class PaddleOCREngine:
    """Optional local PP-OCRv5 adapter.

    PP-OCRv5's Arabic-family recognition model explicitly includes Persian and English. This adapter
    intentionally uses a lazy import because PaddlePaddle wheels are platform/Python-version specific.
    """

    name = "paddleocr"

    def __init__(self, *, lang: str = "fa") -> None:
        try:
            from paddleocr import PaddleOCR  # type: ignore
        except ImportError as exc:
            raise RuntimeError("Install PaddleOCR + a compatible PaddlePaddle runtime") from exc
        self.lang = lang
        try:
            self.ocr = PaddleOCR(
                lang=lang,
                use_doc_orientation_classify=False,
                use_doc_unwarping=False,
                use_textline_orientation=False,
            )
            self.api = "v3"
        except TypeError:
            # Compatibility with older releases.
            self.ocr = PaddleOCR(lang=lang, use_angle_cls=False, show_log=False)
            self.api = "legacy"
        self.preprocess = PreprocessOptions(scale=2.0, clahe=True)

    def extract(self, image_path: str | Path, *, region: BBox | None = None) -> OCRPage:
        import numpy as np

        image, (ox, oy), scale = preprocess_for_ocr(image_path, region=region, options=self.preprocess)
        arr = np.asarray(image)
        tokens: list[OCRToken] = []

        if self.api == "legacy":
            result = self.ocr.ocr(arr, cls=False)
            lines = result[0] if result and isinstance(result[0], list) else result
            for item in lines or []:
                quad, rec = item
                text, confidence = rec
                xs = [p[0] for p in quad]
                ys = [p[1] for p in quad]
                tokens.append(
                    OCRToken(
                        text=str(text),
                        confidence=float(confidence),
                        bbox=BBox(
                            int(min(xs) / scale + ox),
                            int(min(ys) / scale + oy),
                            int(max(xs) / scale + ox),
                            int(max(ys) / scale + oy),
                        ),
                    )
                )
        else:
            # PaddleOCR v3 result objects are deliberately normalized through their JSON representation.
            results = self.ocr.predict(arr)
            for result in results:
                payload = getattr(result, "json", None)
                if callable(payload):
                    payload = payload()
                if not isinstance(payload, dict):
                    continue
                res = payload.get("res", payload)
                texts = res.get("rec_texts", [])
                scores = res.get("rec_scores", [])
                boxes = res.get("rec_boxes", [])
                for text, confidence, box in zip(texts, scores, boxes):
                    x1, y1, x2, y2 = map(float, box)
                    tokens.append(
                        OCRToken(
                            text=str(text),
                            confidence=float(confidence),
                            bbox=BBox(
                                int(x1 / scale + ox), int(y1 / scale + oy),
                                int(x2 / scale + ox), int(y2 / scale + oy),
                            ),
                        )
                    )

        return OCRPage(
            engine=self.name,
            image_path=str(image_path),
            tokens=tuple(tokens),
            raw_text=" ".join(t.text for t in tokens),
            metadata={"lang": self.lang, "api": self.api, "region": region.as_tuple() if region else None},
        )
