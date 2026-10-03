# Project audit — v0.4

This audit reviewed the project from ingestion through query output before adding the next extraction stage.

## What is structurally sound
- Raw Telegram evidence is persisted before OCR.
- OCR is isolated behind engine contracts; paid providers are not required.
- Supplier-specific regions are supported instead of relying on full-page OCR.
- Product/price normalization is deterministic and separate from recognition.
- Price history is append-only and best-price ranking excludes review-flagged offers.
- Existing tests passed before the v0.4 changes (25/25).

## Gaps found during review
1. **No row/cell segmentation layer.** OCR was still mostly region-level, so adjacent rows could bleed into each other.
2. **Approximate supplier crops could include neighboring brand columns.** This was visible in the Fardad sample.
3. **Critical price cells used the same OCR policy as model text.** Digits should be recognized separately with a restricted alphabet.
4. **Memory parsing was brittle when OCR glued model/network digits to storage/RAM**, e.g. `C7164/4` or `S12/124G`.
5. **Tiny OCR artifacts could become plausible prices**, e.g. `1` -> 1,000 toman.
6. Backfill album compaction, automatic source supersession, DB migrations, and production review UI are still pending.
7. The current ground-truth dataset is too small for a production accuracy claim.

## v0.4 fixes
- Added grid-based row/cell segmentation with source-space bounding boxes.
- Added supplier-region x-boundary snapping to strong full-page table rules.
- Added row OCR extraction primitives.
- Added cell-type-specific Tesseract OCR: model text and numeric price cells use different policies.
- Added digit-only OCR for price cells with 10x upscale.
- Added conservative OCR repair for digit contexts only.
- Reworked memory parsing around a valid RAM/storage catalog and OCR-glued suffixes.
- Rejects tiny numeric OCR artifacts at the structured-row layer instead of turning them into prices.
- Added real-fixture segmentation benchmarks and overlays.

## Real-data verification
On `1000015276.jpg` (mobile_hitech), the segmented Xiaomi row corresponding to Note 15 Pro produced:

- RAM: 12 GB — exact
- Storage: 512 GB — exact
- Network: 4G — exact
- Cash price: 116,000,000 toman — exact
- Credit price: 117,000,000 toman — exact

All five business-critical fields in this probe match the manually verified ground truth. This is one verified row, not a global accuracy claim.

## Next gate
The next meaningful stage is not another OCR engine. It is **structured row reconstruction at scale**:

1. define column schemas per supplier/template,
2. run model/color/price OCR per cell,
3. canonicalize models through the catalog,
4. score each field independently,
5. compare extracted rows against the benchmark ground truth,
6. route disagreements/low-confidence fields to review.
