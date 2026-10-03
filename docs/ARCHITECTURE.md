# Architecture v0.3

## Non-negotiable rules
1. Raw Telegram evidence is immutable.
2. Every normalized field keeps its raw value and evidence location.
3. No component may silently invent or 'repair' a price from market history.
4. Low-confidence fields are re-cropped/re-read independently; do not reprocess an entire image unnecessarily.
5. Price changes are append-only versions, never destructive updates.
6. Supplier-specific parsers may optimize known templates, but generic fallback must always exist.
7. OCR is open-source/offline by default.

## Pipeline
1. Telegram collector: new/edit/album/backfill/reconciliation.
2. Raw evidence store: message metadata + original media.
3. List classifier: reject non-price-list posts cheaply.
4. Template fingerprint: supplier/layout family detection.
5. Layout/table analysis: sections, rows, cells, bounding boxes.
6. OSS OCR ensemble: PaddleOCR PP-OCRv5 + RapidOCR/EasyOCR challengers + Tesseract fallback.
7. Field parser: model/memory/network/color/price/metadata.
8. Entity resolution: aliases + catalog + fuzzy candidate generation.
9. Validation: OCR agreement, catalog rules, temporal range, cross-supplier checks.
10. Escalation: alternate crop/preprocessing/OSS recognizer, then human review.
11. Offer store: append-only versions + current view.
12. Query engine: exact variant-aware comparisons with source citations.

## Confidence strategy
Confidence is not a single OCR number. Compute field-level confidence from:
- OCR engine confidence and engine agreement
- lexical/catalog consistency
- supplier-template consistency
- price plausibility and digit agreement
- temporal consistency versus same supplier/variant
- cross-supplier consistency

Any suspicious price must be re-read from the price-cell crop before acceptance.

## Storage implementation status
The repository has an append-only `offer_versions` table and explicit `active/superseded_at` state.
Historical rows remain in the database after supersession; no price update mutates an old observation in place.

## Collector implementation status
A Telethon adapter exists for realtime new messages, albums, edits and bounded backfill. Raw message
metadata and downloaded media are persisted before extraction. Replays are idempotent; changed envelopes
are versioned rather than overwriting the first observation.

## Cheap list triage
A structural, OCR-free classifier uses table/grid evidence to reject obvious non-list images. It is only a
triage stage: uncertain content must escalate rather than be discarded. Real negative Telegram samples are
still needed before tuning production thresholds.
