# HH Price Intelligence

HamiHamrah Market Intelligence: a Telegram-first wholesale mobile price intelligence pipeline.

## Phase 0 goals
- Preserve raw Telegram evidence.
- Detect true price-list images before OCR.
- Extract structured offers with field-level confidence.
- Normalize supplier-specific product aliases into canonical variants.
- Benchmark engines on real competitor lists before production selection.
- Keep provenance for every answer: supplier, Telegram message, source image, crop, parser version.

## Current scaffold
- Domain schema for suppliers, products, offers and extraction evidence.
- Deterministic Persian/English normalization utilities.
- Price parsing with support for CALL / soon / *** / ranges.
- Benchmark metric runner focused on exact field correctness.
- Initial 9 competitor images included as benchmark fixtures.
- FastAPI health/query skeleton.
- Docker Compose skeleton for Postgres + MinIO.

## Benchmark principle
Do not optimize generic OCR character accuracy. Optimize business-critical exact matches:
`model`, `RAM`, `storage`, `network`, `color`, `price`, `variant`, and final best-price-query correctness.

## Quick start
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
pytest
uvicorn hhpi.api.app:app --reload
```

## Roadmap
See `docs/ARCHITECTURE.md` and `docs/BENCHMARK_PLAN.md`.

## Phase 0.3 implemented
- OCR-free structural/table profiling with OpenCV.
- Layout overlays and supplier-template fingerprint inputs for all benchmark images.
- OSS-only OCR adapter stack: PaddleOCR, RapidOCR, EasyOCR, Tesseract.
- Working local Tesseract `fas+eng` engine with crop/upscale/contrast preprocessing.
- Field-level OCR consensus/escalation primitives.
- Deterministic catalog alias resolver with conservative fuzzy fallback.
- Price anomaly validator that flags but never auto-corrects source values.
- Expanded unit-test suite.

## Runnable demo query
The seed benchmark can be loaded into a local SQLite database:
```bash
PYTHONPATH=src python scripts/seed_demo_db.py
DATABASE_URL=sqlite+pysqlite:///./benchmarks/demo.sqlite uvicorn hhpi.api.app:app --reload
```
Then query, for example, `GET /v1/best-price?model=Note%2015&storage_gb=256&ram_gb=8&network=4G&color=مشکی`.
The verified seed currently ranks the Fardad Hamrah range first (80.0–80.5M), followed by ani_mob
(80.5M) and alerasolshop (81.0M) for the black 8/256 4G variant in the supplied screenshots.


## OCR policy
OCR is now open-source/offline by default. The preferred stack is PaddleOCR PP-OCRv5 + RapidOCR/EasyOCR challengers with Tesseract as a deterministic local fallback. Paid OCR APIs are excluded from the default architecture. See `docs/OSS_OCR_STACK.md`.

Run the currently available local benchmark:
```bash
pip install -e '.[ocr-tesseract]'
PYTHONPATH=src python scripts/inspect_oss_ocr.py
PYTHONPATH=src python scripts/run_oss_ocr_benchmark.py
```
