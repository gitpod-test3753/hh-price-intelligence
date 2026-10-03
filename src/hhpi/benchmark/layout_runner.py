from __future__ import annotations

import json
from pathlib import Path

from hhpi.layout.grid import profile_image, render_overlay


def run_layout_benchmark(fixtures: Path, output_root: Path) -> list[dict]:
    profiles_dir = output_root / "layout_profiles"
    overlays_dir = output_root / "layout_overlays"
    profiles_dir.mkdir(parents=True, exist_ok=True)
    overlays_dir.mkdir(parents=True, exist_ok=True)

    summary: list[dict] = []
    for image_path in sorted(fixtures.glob("*.jpg")):
        profile = profile_image(image_path)
        overlay_path = overlays_dir / image_path.name
        boxes = render_overlay(image_path, overlay_path)
        payload = profile.to_dict() | {"file": image_path.name, "regions": [b.as_tuple() for b in boxes]}
        (profiles_dir / f"{image_path.stem}.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        summary.append(payload)

    (output_root / "layout_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return summary
