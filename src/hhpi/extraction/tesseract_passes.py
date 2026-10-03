from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from hhpi.layout.models import BBox
from .contracts import OCRPage
from .preprocess import PreprocessOptions
from .tesseract_engine import TesseractEngine


@dataclass(frozen=True)
class TesseractPass:
    pass_id: str
    languages: str
    psm: int
    preprocess: PreprocessOptions


DEFAULT_TESSERACT_PASSES: tuple[TesseractPass, ...] = (
    TesseractPass(
        "mixed_block",
        "fas+eng",
        6,
        PreprocessOptions(scale=3.0, clahe=True),
    ),
    TesseractPass(
        "mixed_sparse",
        "fas+eng",
        11,
        PreprocessOptions(scale=3.0, clahe=True),
    ),
    TesseractPass(
        "english_block",
        "eng",
        6,
        PreprocessOptions(scale=3.0, clahe=True),
    ),
    TesseractPass(
        "mixed_grid_removed",
        "fas+eng",
        6,
        PreprocessOptions(scale=3.0, clahe=True, threshold=True, remove_grid_lines=True),
    ),
)


def extract_tesseract_passes(
    image_path: str | Path,
    *,
    region: BBox | None = None,
    passes: tuple[TesseractPass, ...] = DEFAULT_TESSERACT_PASSES,
) -> tuple[OCRPage, ...]:
    pages: list[OCRPage] = []
    for spec in passes:
        engine = TesseractEngine(
            languages=spec.languages,
            psm=spec.psm,
            preprocess=spec.preprocess,
        )
        page = engine.extract(image_path, region=region)
        page.metadata["pass_id"] = spec.pass_id
        pages.append(page)
    return tuple(pages)

ROW_TESSERACT_PASS = TesseractPass(
    "english_single_row",
    "eng",
    13,
    PreprocessOptions(scale=8.0, clahe=False, threshold=False, remove_grid_lines=False),
)
