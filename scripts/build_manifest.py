import json
from pathlib import Path
from hhpi.benchmark.manifest import build_manifest

root = Path(__file__).resolve().parents[1]
fixtures = root / "benchmarks" / "fixtures" / "raw"
out = root / "benchmarks" / "manifest.json"
out.write_text(json.dumps(build_manifest(fixtures), ensure_ascii=False, indent=2), encoding="utf-8")
print(out)
