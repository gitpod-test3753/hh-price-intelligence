from __future__ import annotations

import json
from pathlib import Path

from hhpi.layout.fingerprint import fingerprint_image, similarity


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    fixtures = sorted((root / "benchmarks" / "fixtures" / "raw").glob("*.jpg"))
    fps = {p.name: fingerprint_image(p) for p in fixtures}
    matrix = {
        a: {b: similarity(fps[a], fps[b]) for b in fps}
        for a in fps
    }
    out = root / "benchmarks" / "template_similarity.json"
    out.write_text(json.dumps(matrix, indent=2), encoding="utf-8")
    print(out)
