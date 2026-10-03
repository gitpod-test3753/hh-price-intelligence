from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image

from hhpi.extraction.tesseract_passes import extract_tesseract_passes
from hhpi.layout.models import BBox


def bbox_from_fraction(image_path: Path, frac: list[float]) -> BBox:
    with Image.open(image_path) as im:
        w, h = im.size
    return BBox(round(frac[0] * w), round(frac[1] * h), round(frac[2] * w), round(frac[3] * h))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fixtures", default="benchmarks/fixtures/raw")
    ap.add_argument("--profiles", default="benchmarks/supplier_profiles/known_regions.json")
    ap.add_argument("--out", default="benchmarks/ocr_results/multipass")
    args = ap.parse_args()

    fixtures = Path(args.fixtures)
    profiles = json.loads(Path(args.profiles).read_text(encoding="utf-8"))
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    index: list[dict] = []
    for image_id, spec in profiles.items():
        image_path = fixtures / image_id
        for region_name, frac in spec["regions"].items():
            bbox = bbox_from_fraction(image_path, frac)
            pages = extract_tesseract_passes(image_path, region=bbox)
            for page in pages:
                pass_id = page.metadata["pass_id"]
                payload = {
                    "image_id": image_id,
                    "supplier_id": spec["supplier_id"],
                    "region": region_name,
                    "bbox": bbox.as_tuple(),
                    "engine": page.engine,
                    "pass_id": pass_id,
                    "raw_text": page.raw_text,
                    "tokens": [
                        {"text": t.text, "confidence": t.confidence, "bbox": t.bbox.as_tuple()}
                        for t in page.tokens
                    ],
                }
                path = out / f"{Path(image_id).stem}.{region_name}.{pass_id}.json"
                path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
                index.append(
                    {
                        "file": path.name,
                        "image_id": image_id,
                        "supplier_id": spec["supplier_id"],
                        "region": region_name,
                        "pass_id": pass_id,
                        "token_count": len(page.tokens),
                    }
                )

    (out / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(index, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
