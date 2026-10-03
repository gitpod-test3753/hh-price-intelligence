from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from hhpi.layout.models import BBox
from hhpi.layout.segmentation import TableRow, TableSegmentation
from .contracts import OCREngine, OCRPage


@dataclass(frozen=True)
class RowOCRResult:
    row_index: int
    bbox: BBox
    page: OCRPage


class RowOCRExtractor:
    """Run OCR independently per segmented row.

    Dense full-sheet OCR tends to merge adjacent rows and columns. Isolating each row lets engines use
    single-line assumptions and prevents a mistake in one row from shifting the rest of the document.
    """

    def __init__(self, engine: OCREngine) -> None:
        self.engine = engine

    def extract_rows(
        self,
        image_path: str | Path,
        segmentation: TableSegmentation,
        *,
        include_empty: bool = False,
    ) -> tuple[RowOCRResult, ...]:
        results: list[RowOCRResult] = []
        for row in segmentation.rows:
            page = self.engine.extract(image_path, region=row.bbox)
            if include_empty or (page.raw_text and page.raw_text.strip()):
                results.append(RowOCRResult(row_index=row.index, bbox=row.bbox, page=page))
        return tuple(results)
