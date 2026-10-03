from __future__ import annotations

import json
from pathlib import Path

import cv2

from hhpi.extraction.structured_rows import TesseractStructuredRowReader
from hhpi.layout.models import BBox
from hhpi.layout.segmentation import refine_region_to_grid, segment_table

ROOT = Path(__file__).resolve().parents[1]
IMAGE = ROOT / "benchmarks" / "fixtures" / "raw" / "1000015276.jpg"
PROFILES = ROOT / "benchmarks" / "supplier_profiles" / "known_regions.json"
OUT = ROOT / "benchmarks" / "structured_row_probe.json"


def main() -> None:
    profiles = json.loads(PROFILES.read_text(encoding="utf-8"))
    profile = profiles[IMAGE.name]
    image = cv2.imread(str(IMAGE))
    h, w = image.shape[:2]
    q = profile["regions"]["xiaomi"]
    raw = BBox(int(q[0] * w), int(q[1] * h), int(q[2] * w), int(q[3] * h))
    region = refine_region_to_grid(IMAGE, raw)
    seg = segment_table(IMAGE, region=region)
    reader = TesseractStructuredRowReader()
    roles = ("model", "color", "cash", "credit")

    rows = []
    for row in seg.rows:
        if len(row.cells) < len(roles):
            continue
        candidate = reader.read(IMAGE, row, roles=roles)
        payload = {
            "row_index": candidate.row_index,
            "bbox": row.bbox.as_tuple(),
            "model": candidate.raw_model_text,
            "ram_gb": candidate.ram_gb,
            "storage_gb": candidate.storage_gb,
            "network": candidate.network,
            "color": candidate.color_text,
            "cash": candidate.cash.model_dump(mode="json") if candidate.cash else None,
            "credit": candidate.credit.model_dump(mode="json") if candidate.credit else None,
            "evidence": candidate.evidence,
        }
        rows.append(payload)

    result = {
        "image_id": IMAGE.name,
        "supplier_id": profile["supplier_id"],
        "schema": roles,
        "rows": rows,
    }
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    # Print the rows most relevant to the current benchmark.
    hits = [r for r in rows if "NOTE" in r["model"].upper() and "15" in r["model"]]
    print(json.dumps(hits, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
