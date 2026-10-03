# Engineering status — v0.3

## Completed
- 9 supplied competitor price-list images mounted as benchmark fixtures.
- OCR-free structural profiler and grid/table overlays for every fixture.
- Structural template fingerprint and similarity matrix.
- Cheap price-list triage classifier with an explicit `uncertain` state.
- OSS-only OCR contract and adapters for PaddleOCR, RapidOCR, EasyOCR and Tesseract.
- Field-level OCR consensus and escalation primitive.
- Persian/English normalization, memory parsing and color aliases.
- Market-aware price parsing including shorthand ranges such as `115000-116`.
- Distinct single/range/cash/credit price semantics.
- Conservative catalog alias resolver.
- Price anomaly validation that flags but never invents/corrects a source price.
- Append-only SQLAlchemy offer store with supersession rather than destructive updates.
- Working variant-aware best-price query engine and FastAPI endpoint.
- Telethon realtime/backfill collector adapter plus immutable raw-evidence store.
- Manually verified Note 15 seed dataset from multiple supplied competitor sheets.
- Local SQLite demo database generated from the verified seed.
- 25 automated tests passing.

## Verified demo answer from supplied screenshots
For `Note 15 / 8GB / 256GB / 4G / black` in the current verified seed:
1. `fardadhamrah` — 80.0–80.5M toman range
2. `ani_mob` — 80.5M toman
3. `alerasolshop` — 81.0M toman

This is a benchmark seed result, not yet a live Telegram result.

## OSS OCR decision
Paid OCR services are removed from the default path. Tesseract is already runnable locally; PaddleOCR PP-OCRv5 is the preferred primary once deployed in a compatible worker image, with RapidOCR/EasyOCR as independent challengers.

## Next engineering gate
Expand manually verified row crops across suppliers, run all available OSS engines on identical regions, and choose the best two-engine ensemble by price/model/RAM/storage/color exact accuracy and cheapest-query correctness.


## First live OSS OCR run
The current environment has Tesseract 5 with both `fas` and `eng` trained data installed. The local benchmark was executed against four known Xiaomi supplier regions. On the Fardad Hamrah crop, local OCR recovered repeated `Note 15` rows and the `80000-80500` price range; on the Alerasol crop it recovered `Note 15 ... Black ... 81000`. These are raw OCR observations, not yet counted as final structured row accuracy.

Dense full-sheet OCR remains intentionally disabled as the main path: supplier/template cropping materially improves recognition and is now part of the default OCR design.
