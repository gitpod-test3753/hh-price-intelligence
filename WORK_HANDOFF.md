# Work handoff — HH Price Intelligence v0.4

## Goal
Build an offline/open-source OCR pipeline that monitors Telegram supplier channels, detects true price lists, extracts exact phone variants and prices with provenance, normalizes supplier naming, and answers queries such as “today, where is Note 15 8/256 black cheapest?”.

## Current verified state
- 9 real competitor price-list screenshots are included as benchmark fixtures.
- Telegram ingestion contract, immutable evidence storage, append-only price history, catalog normalization, best-price query engine, and FastAPI endpoint exist.
- Paid OCR is excluded from the default architecture.
- OSS OCR adapters exist for PaddleOCR, RapidOCR, EasyOCR, and Tesseract.
- Tesseract `fas+eng` is runnable locally in the current environment.
- Supplier/template-aware cropping and structural grid detection are implemented.
- Row/cell segmentation is implemented with source-space bounding boxes.
- Price cells have a digit-focused OCR path and model cells use a separate OCR policy.
- One real Note 15 Pro row from `1000015276.jpg` was manually verified end-to-end: RAM 12, storage 512, network 4G, cash 116M, credit 117M.
- Current automated test suite: 32/32 passing.

## Where the project is actually stuck
The main bottleneck is no longer generic OCR. It is **structured row reconstruction at scale** across supplier-specific table layouts.

Problems to solve next:
1. Define explicit column schemas for each supplier/template instead of inferring every column on every run.
2. Segment rows robustly while avoiding header/subheader bleed and neighboring brand sections.
3. OCR each cell according to its semantic type: model, memory, color, cash price, credit price, warranty/registration.
4. Reconstruct a row only when field-level evidence is coherent.
5. Score model/RAM/storage/network/color/price independently.
6. Compare extracted rows against manually verified ground truth and measure exact business-field accuracy.
7. Route only disagreements/low-confidence cells to re-crop / alternate OSS OCR / human review.

## Immediate implementation plan
### A. Supplier template schema
Create `SupplierTemplateSchema` with normalized coordinates / snapped column rules and semantic column types.

### B. Structured row extractor
Implement:
`template crop -> grid snap -> row boxes -> cell boxes -> field-specific OCR -> normalization -> row candidate -> confidence`

### C. Benchmark ground truth
Expand ground truth from the currently verified rows to at least 50 rows across 4+ suppliers, prioritizing Xiaomi/Samsung/iPhone dense sections.

### D. Exact metrics
Track:
- model exact match
- RAM exact match
- storage exact match
- network exact match
- color exact match
- cash price exact match
- credit price exact match
- full variant exact match
- row recall / false-row rate
- final cheapest-query correctness

### E. Engine evaluation
Use OSS-only engines. Prefer PaddleOCR PP-OCRv5 as the primary candidate when its worker image is available; keep Tesseract as deterministic fallback and RapidOCR/EasyOCR as challengers.

## Important rules
- Never auto-correct a source price from market expectations/history; only flag suspicious values and re-read evidence.
- Preserve raw source text and crops for every normalized field.
- Never overwrite historical offers; supersede with new versions.
- Do not compare cash vs credit prices as if they were the same price type.
- Product matching must be deterministic-first (aliases/catalog/fuzzy), not LLM-first.

## Useful files
- `docs/AUDIT_V0_4.md` — current audit and identified gaps
- `docs/OSS_OCR_STACK.md` — open-source OCR strategy
- `benchmarks/fixtures/raw/` — real supplier screenshots
- `benchmarks/segmentation/overlays/` — segmentation visual checks
- `scripts/run_segmentation_benchmark.py`
- `scripts/run_structured_row_probe.py`
- `src/hhpi/` — implementation
- `tests/` — regression suite

## First command in Work
Run:
```bash
pytest -q
```
Expected current result: `32 passed`.

Then inspect `docs/AUDIT_V0_4.md` and continue from “Next gate”.
