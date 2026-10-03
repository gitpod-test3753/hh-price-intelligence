from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image

from hhpi.extraction.oss_registry import discover_oss_engines
from hhpi.extraction.tesseract_engine import TesseractEngine
from hhpi.layout.models import BBox


def _bbox_from_fraction(image_path: Path, frac: list[float]) -> BBox:
    with Image.open(image_path) as im:
        w, h = im.size
    x1, y1, x2, y2 = frac
    return BBox(round(w * x1), round(h * y1), round(w * x2), round(h * y2))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixtures", default="benchmarks/fixtures/raw")
    parser.add_argument("--profiles", default="benchmarks/supplier_profiles/known_regions.json")
    parser.add_argument("--out", default="benchmarks/ocr_results")
    args = parser.parse_args()

    fixtures = Path(args.fixtures)
    profiles = json.loads(Path(args.profiles).read_text(encoding="utf-8"))
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    availability = [a.__dict__ for a in discover_oss_engines()]
    (out / "availability.json").write_text(
        json.dumps(availability, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    engine = TesseractEngine(languages="fas+eng", psm=6)
    if not engine.is_available():
        raise SystemExit("Tesseract is not available in this environment")

    summary: list[dict] = []
    for filename, profile in profiles.items():
        image_path = fixtures / filename
        for region_name, fraction in profile["regions"].items():
            bbox = _bbox_from_fraction(image_path, fraction)
            page = engine.extract(image_path, region=bbox)
            payload = {
                "image_id": filename,
                "supplier_id": profile["supplier_id"],
                "region": region_name,
                "bbox": bbox.as_tuple(),
                "engine": page.engine,
                "token_count": len(page.tokens),
                "mean_confidence": (
                    round(sum(t.confidence for t in page.tokens) / len(page.tokens), 4)
                    if page.tokens
                    else 0.0
                ),
                "raw_text": page.raw_text,
                "tokens": [
                    {
                        "text": t.text,
                        "confidence": round(t.confidence, 4),
                        "bbox": t.bbox.as_tuple(),
                    }
                    for t in page.tokens
                ],
            }
            target = out / f"{Path(filename).stem}.{region_name}.tesseract.json"
            target.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            summary.append({k: v for k, v in payload.items() if k not in {"raw_text", "tokens"}})

    (out / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
