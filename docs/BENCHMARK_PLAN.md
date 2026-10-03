# Benchmark Lab Plan — OSS only

## Dataset
Start with the 9 competitor images already supplied. Expand to 30–50 lists and 1,000–3,000 manually verified rows before choosing the final production ensemble.

## Ground-truth row schema
- supplier_id
- image_id
- row_id
- brand
- model_raw
- model_canonical
- ram_gb
- storage_gb
- network
- color_raw
- color_canonical
- region / part number
- warranty / registration
- condition
- price_raw
- normalized price
- bbox for row and price cell

## Engines to benchmark
All default candidates are local/free/open-source:
- PaddleOCR PP-OCRv5 (primary target; Persian supported by Arabic-family recognizer)
- RapidOCR with PP-OCRv5 Arabic-family ONNX recognition model
- EasyOCR (`fa`, `en`)
- Tesseract 5 (`fas+eng`) with supplier/template cropping

Table/layout structure is handled separately with OpenCV and, when useful, PaddleOCR table/layout components. Keeping structure detection separate lets us choose the best recognizer per field without forcing one monolithic document parser.

## Metrics
Primary:
- price exact match
- model exact match
- RAM exact match
- storage exact match
- color exact match
- network exact match
- complete variant exact match
- row recall
- false-row rate
- best-price query correctness

Secondary:
- latency / image
- CPU/GPU memory
- re-read/escalation rate
- human-review rate

## Acceptance gates
Do not ship based on average OCR CER/WER alone.
Initial gate proposal:
- price exact >= 99.5% on auto-accepted rows
- storage/RAM exact >= 99.5%
- false best-price answer = 0 on benchmark
- every accepted price has traceable source evidence
