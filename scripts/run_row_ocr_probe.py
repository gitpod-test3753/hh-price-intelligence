from __future__ import annotations

import json
from pathlib import Path

import cv2

from hhpi.extraction.preprocess import PreprocessOptions
from hhpi.extraction.tesseract_engine import TesseractEngine
from hhpi.layout.models import BBox
from hhpi.layout.segmentation import refine_region_to_grid, segment_table

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "benchmarks" / "fixtures" / "raw"
PROFILES = ROOT / "benchmarks" / "supplier_profiles" / "known_regions.json"
OUT = ROOT / "benchmarks" / "row_ocr_probe"


def _bbox(path: Path, q: list[float]) -> BBox:
    image = cv2.imread(str(path))
    h, w = image.shape[:2]
    return BBox(int(q[0] * w), int(q[1] * h), int(q[2] * w), int(q[3] * h))


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    profiles = json.loads(PROFILES.read_text(encoding="utf-8"))
    engine = TesseractEngine(
        languages="eng",
        psm=13,
        preprocess=PreprocessOptions(scale=8.0, clahe=False, threshold=False, remove_grid_lines=False),
    )
    # Probe a small representative set; this is a smoke benchmark, not the final OCR accuracy score.
    selected = ("1000015278.jpg", "1000015276.jpg")
    report = []
    for filename in selected:
        profile = profiles[filename]
        path = FIXTURES / filename
        raw = _bbox(path, profile["regions"]["xiaomi"])
        region = refine_region_to_grid(path, raw)
        seg = segment_table(path, region=region)
        rows = []
        for row in seg.rows:
            page = engine.extract(path, region=row.bbox)
            text = (page.raw_text or "").strip()
            if text:
                rows.append({
                    "row_index": row.index,
                    "bbox": row.bbox.as_tuple(),
                    "text": text,
                    "mean_confidence": round(
                        sum(t.confidence for t in page.tokens) / len(page.tokens), 4
                    ) if page.tokens else 0.0,
                })
        payload = {
            "image_id": filename,
            "supplier_id": profile["supplier_id"],
            "raw_region": raw.as_tuple(),
            "region": region.as_tuple(),
            "row_count": len(seg.rows),
            "recognized_rows": len(rows),
            "rows": rows,
        }
        (OUT / f"{Path(filename).stem}.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        report.append({k: v for k, v in payload.items() if k != "rows"})
    (OUT / "summary.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
