from __future__ import annotations

import json
from pathlib import Path

import cv2

from hhpi.layout.models import BBox
from hhpi.layout.segmentation import refine_region_to_grid, render_segmentation_overlay, segment_table

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "benchmarks" / "fixtures" / "raw"
PROFILES = ROOT / "benchmarks" / "supplier_profiles" / "known_regions.json"
OUT = ROOT / "benchmarks" / "segmentation"


def to_bbox(image_path: Path, values: list[float]) -> BBox:
    image = cv2.imread(str(image_path))
    h, w = image.shape[:2]
    return BBox(int(round(values[0] * w)), int(round(values[1] * h)), int(round(values[2] * w)), int(round(values[3] * h)))


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    overlays = OUT / "overlays"
    overlays.mkdir(exist_ok=True)
    profiles = json.loads(PROFILES.read_text(encoding="utf-8"))
    summary = []
    for filename, profile in profiles.items():
        image_path = FIXTURES / filename
        schemas = profile.get("schemas", {})
        for region_name, normalized in profile["regions"].items():
            schema = schemas.get(region_name, {})
            raw_region = to_bbox(image_path, normalized)
            snap = schema.get("snap_to_grid", True)
            region = refine_region_to_grid(image_path, raw_region) if snap else raw_region
            splits = tuple(schema.get("column_splits", ())) or None
            seg = segment_table(image_path, region=region, column_splits=splits)
            payload = {
                "image_id": filename,
                "supplier_id": profile["supplier_id"],
                "region_name": region_name,
                "raw_region": raw_region.as_tuple(),
                "region": region.as_tuple(),
                "rows": len(seg.rows),
                "columns": max((len(r.cells) for r in seg.rows), default=0),
                "horizontal_separators": len(seg.horizontal_separators),
                "vertical_separators": len(seg.vertical_separators),
                "segmentation": seg.to_dict(),
            }
            out_json = OUT / f"{Path(filename).stem}.{region_name}.json"
            out_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            overlay = overlays / f"{Path(filename).stem}.{region_name}.jpg"
            render_segmentation_overlay(image_path, overlay, seg)
            summary.append({k: v for k, v in payload.items() if k != "segmentation"})
    (OUT / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
