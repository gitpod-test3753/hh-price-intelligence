from __future__ import annotations

import json

from hhpi.extraction.oss_registry import discover_oss_engines
from hhpi.extraction.tesseract_engine import TesseractEngine


if __name__ == "__main__":
    availability = [x.__dict__ for x in discover_oss_engines()]
    info = {"engines": availability}
    if TesseractEngine.is_available():
        engine = TesseractEngine()
        info["tesseract_languages"] = engine.installed_languages()
    print(json.dumps(info, ensure_ascii=False, indent=2))
