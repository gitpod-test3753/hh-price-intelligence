# OSS-only OCR stack

The production OCR path is now intentionally **offline/open-source first**. Paid OCR APIs are not part of the default architecture.

## Selected stack

1. **PaddleOCR / PP-OCRv5** — preferred primary recognizer once the deployment image has a compatible PaddlePaddle runtime. The official PP-OCRv5 multilingual docs list Persian (`fa`) in the Arabic-family recognition model together with English. PaddleOCR is Apache-2.0.
2. **RapidOCR** — lightweight ONNX/OpenVINO deployment path for Paddle-derived models. For Persian we must load the Arabic-family PP-OCRv5 recognizer/dictionary, not the default Chinese/English bundle. RapidOCR and the redistributed Paddle-derived model artifacts are Apache-2.0.
3. **EasyOCR** — secondary independent recognizer. Its Arabic-family model explicitly includes `fa` + `en`; code is Apache-2.0.
4. **Tesseract 5** — deterministic local fallback/baseline with `fas+eng`. Tesseract and official `tessdata` are Apache-2.0.

## Why Tesseract remains useful

Full-page recognition on a 4-column wholesale sheet is poor. The same engine becomes materially useful after:

`known supplier template -> brand region crop -> 2–3x upscale -> contrast normalization -> OCR`

On the supplied Fardad Hamrah image, the targeted Xiaomi crop reads repeated Note 15 rows and price ranges such as `80000-80500` without any cloud API. The pipeline therefore treats layout/template intelligence as part of OCR quality, not just preprocessing.

## Free ensemble policy

```text
PaddleOCR PP-OCRv5
        +
RapidOCR PP-OCRv5 ONNX
        +
EasyOCR fa+en
        +
Tesseract fas+eng
        |
        v
field-level consensus
        |
        +--> high agreement: accept
        |
        +--> disagreement: re-crop / alternate preprocessing / review queue
```

No external value is invented from price history. Historical/market data may only mark a recognition as suspicious and trigger re-reading.

## Deployment notes

PaddlePaddle wheels are platform and Python-version specific, so PaddleOCR is a lazy optional adapter. Keep the main service independent from that runtime. A production worker can run Python 3.10/3.11 in its own container while FastAPI/database services use another supported version.

## Benchmark order

Before choosing the final two-engine production ensemble, measure on the HamiHamrah benchmark:

- price exact match (highest priority)
- model exact match
- RAM/storage exact match
- color exact match
- row recall
- cheapest-query correctness
- latency on CPU and GPU

Paid APIs are excluded unless the product owner explicitly changes this decision later.
