# Benchmark Lab v0.3

The benchmark lab has an OCR-free structural stage before OCR and now an actually runnable open-source OCR baseline.

## Stage A — structural profiling
For every source image we compute document dimensions/aspect ratio, foreground density, horizontal/vertical grid-line density, normalized line coordinates, candidate table regions and a cheap table-likelihood score.

This supports price-list triage, supplier-template fingerprints, region routing/cropping and template-drift detection.

Outputs:
- `benchmarks/layout_profiles/*.json`
- `benchmarks/layout_overlays/*.jpg`
- `benchmarks/layout_summary.json`

Run with:
```bash
PYTHONPATH=src python scripts/run_layout_benchmark.py
```

## Stage B — OSS OCR adapters
The common `OCREngine` contract now has adapters for PaddleOCR, RapidOCR, EasyOCR and Tesseract. Tesseract is executable in the current development environment and uses Persian + English trained data.

The benchmark intentionally OCRs supplier/brand regions rather than whole dense sheets. On the supplied Fardad Hamrah Xiaomi crop, this already recovers repeated Note 15 rows and `80000-80500` price ranges locally.

Run with:
```bash
PYTHONPATH=src python scripts/inspect_oss_ocr.py
PYTHONPATH=src python scripts/run_oss_ocr_benchmark.py
```

Outputs:
- `benchmarks/ocr_results/environment.json`
- `benchmarks/ocr_results/summary.json`
- per-image token/evidence JSON

## Stage C — field-level ensemble
Do not vote on the whole row. Model, RAM, storage, color and especially price are resolved independently. When engines disagree on price, only the price crop is re-read.

## Stage D — validation without invention
Historical and cross-supplier prices may flag an OCR value as suspicious, but never replace the observed value. Re-reading the source crop is mandatory.

## First verified seed set
`benchmarks/ground_truth/seed_note15.jsonl` contains manually verified Note 15 / Note 15 Pro examples from multiple supplied competitor sheets. It tests the business query before full OCR extraction is complete.

A market-specific parser bug was discovered from the real sheets: suppliers use shorthand ranges such as `115000-116`, meaning 115,000 to 116,000 in the sheet's unit. The parser expands this conservatively before applying the supplier's toman scale.

The domain distinguishes `single`, `range`, `cash`, and `credit` price bases so a cash quote is not silently treated as the same thing as a credit quote.
