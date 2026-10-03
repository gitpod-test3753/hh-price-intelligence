from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

import cv2
import numpy as np

from .models import BBox


@dataclass(frozen=True)
class SegmentConfig:
    horizontal_kernel_ratio: float = 0.42
    vertical_kernel_ratio: float = 0.18
    horizontal_projection_ratio: float = 0.30
    vertical_projection_ratio: float = 0.22
    min_row_px: int = 5
    min_col_px: int = 8
    edge_snap_px: int = 4
    row_padding_px: int = 1
    cell_padding_px: int = 1


@dataclass(frozen=True)
class TableCell:
    row_index: int
    col_index: int
    bbox: BBox

    def to_dict(self) -> dict:
        return {"row_index": self.row_index, "col_index": self.col_index, "bbox": self.bbox.as_tuple()}


@dataclass(frozen=True)
class TableRow:
    index: int
    bbox: BBox
    cells: tuple[TableCell, ...]

    def to_dict(self) -> dict:
        return {
            "index": self.index,
            "bbox": self.bbox.as_tuple(),
            "cells": [c.to_dict() for c in self.cells],
        }


@dataclass(frozen=True)
class TableSegmentation:
    region: BBox
    horizontal_separators: tuple[int, ...]
    vertical_separators: tuple[int, ...]
    rows: tuple[TableRow, ...]
    method: str = "grid_projection"

    def to_dict(self) -> dict:
        return {
            "region": self.region.as_tuple(),
            "horizontal_separators": list(self.horizontal_separators),
            "vertical_separators": list(self.vertical_separators),
            "rows": [r.to_dict() for r in self.rows],
            "method": self.method,
        }


def _read(path: str | Path) -> np.ndarray:
    image = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if image is None:
        raise FileNotFoundError(path)
    return image


def _clip_region(image: np.ndarray, region: BBox | None) -> tuple[np.ndarray, BBox]:
    h, w = image.shape[:2]
    if region is None:
        box = BBox(0, 0, w, h)
    else:
        box = BBox(
            max(0, min(w - 1, int(region.x1))),
            max(0, min(h - 1, int(region.y1))),
            max(1, min(w, int(region.x2))),
            max(1, min(h, int(region.y2))),
        )
    if box.x2 <= box.x1 or box.y2 <= box.y1:
        raise ValueError(f"Invalid region: {region}")
    return image[box.y1 : box.y2, box.x1 : box.x2].copy(), box


def _binary(crop: np.ndarray) -> np.ndarray:
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    # Adaptive threshold copes better with colored supplier sheets than a fixed threshold.
    return cv2.adaptiveThreshold(
        gray,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        31,
        11,
    )


def _merge_adjacent(values: np.ndarray, max_gap: int = 2) -> tuple[int, ...]:
    if values.size == 0:
        return ()
    groups: list[list[int]] = [[int(values[0])]]
    for raw in values[1:]:
        value = int(raw)
        if value <= groups[-1][-1] + max_gap:
            groups[-1].append(value)
        else:
            groups.append([value])
    return tuple(int(round(sum(g) / len(g))) for g in groups)


def _separator_peaks(mask: np.ndarray, *, axis: int, min_span_ratio: float) -> tuple[int, ...]:
    projection = (mask > 0).sum(axis=axis)
    full_span = mask.shape[1] if axis == 1 else mask.shape[0]
    hits = np.flatnonzero(projection >= max(2, int(full_span * min_span_ratio)))
    return _merge_adjacent(hits)


def _snap_edges(coords: tuple[int, ...], extent: int, snap_px: int) -> tuple[int, ...]:
    vals = list(coords)
    if not vals or vals[0] > snap_px:
        vals.insert(0, 0)
    elif vals[0] <= snap_px:
        vals[0] = 0
    if not vals or extent - vals[-1] > snap_px:
        vals.append(extent)
    elif extent - vals[-1] <= snap_px:
        vals[-1] = extent
    # Keep only monotonic unique coordinates.
    out: list[int] = []
    for v in vals:
        v = max(0, min(extent, int(v)))
        if not out or v > out[-1]:
            out.append(v)
    return tuple(out)


def detect_grid_separators(
    image_path: str | Path,
    *,
    region: BBox | None = None,
    config: SegmentConfig | None = None,
) -> tuple[tuple[int, ...], tuple[int, ...], BBox]:
    """Return source-space horizontal and vertical separator coordinates.

    The detector intentionally looks only for long rules. Short text strokes should not become row
    boundaries. Coordinates are always mapped back to the original image so OCR evidence remains auditable.
    """
    config = config or SegmentConfig()
    image = _read(image_path)
    crop, source = _clip_region(image, region)
    binary = _binary(crop)
    h, w = binary.shape

    h_kernel = cv2.getStructuringElement(
        cv2.MORPH_RECT, (max(20, int(w * config.horizontal_kernel_ratio)), 1)
    )
    v_kernel = cv2.getStructuringElement(
        cv2.MORPH_RECT, (1, max(20, int(h * config.vertical_kernel_ratio)))
    )
    horizontal = cv2.morphologyEx(binary, cv2.MORPH_OPEN, h_kernel)
    vertical = cv2.morphologyEx(binary, cv2.MORPH_OPEN, v_kernel)

    ys = _separator_peaks(horizontal, axis=1, min_span_ratio=config.horizontal_projection_ratio)
    xs = _separator_peaks(vertical, axis=0, min_span_ratio=config.vertical_projection_ratio)
    ys = _snap_edges(ys, h, config.edge_snap_px)
    xs = _snap_edges(xs, w, config.edge_snap_px)

    return (
        tuple(source.y1 + y for y in ys),
        tuple(source.x1 + x for x in xs),
        source,
    )


def _intervals(coords: tuple[int, ...], minimum: int) -> tuple[tuple[int, int], ...]:
    out: list[tuple[int, int]] = []
    for a, b in zip(coords, coords[1:]):
        if b - a >= minimum:
            out.append((a, b))
    return tuple(out)


def segment_table(
    image_path: str | Path,
    *,
    region: BBox | None = None,
    config: SegmentConfig | None = None,
) -> TableSegmentation:
    config = config or SegmentConfig()
    ys, xs, source = detect_grid_separators(image_path, region=region, config=config)

    row_intervals = _intervals(ys, config.min_row_px)
    col_intervals = _intervals(xs, config.min_col_px)

    rows: list[TableRow] = []
    for row_index, (y1, y2) in enumerate(row_intervals):
        row_box = BBox(
            source.x1,
            min(y2 - 1, y1 + config.row_padding_px),
            source.x2,
            max(y1 + 1, y2 - config.row_padding_px),
        )
        cells: list[TableCell] = []
        for col_index, (x1, x2) in enumerate(col_intervals):
            cell = BBox(
                min(x2 - 1, x1 + config.cell_padding_px),
                row_box.y1,
                max(x1 + 1, x2 - config.cell_padding_px),
                row_box.y2,
            )
            if cell.width >= config.min_col_px - 2 and cell.height >= config.min_row_px - 2:
                cells.append(TableCell(row_index=row_index, col_index=col_index, bbox=cell))
        rows.append(TableRow(index=row_index, bbox=row_box, cells=tuple(cells)))

    return TableSegmentation(
        region=source,
        horizontal_separators=ys,
        vertical_separators=xs,
        rows=tuple(rows),
    )


def render_segmentation_overlay(
    image_path: str | Path,
    output_path: str | Path,
    segmentation: TableSegmentation,
    *,
    draw_cells: bool = True,
    label_every: int = 5,
) -> None:
    image = _read(image_path)
    r = segmentation.region
    cv2.rectangle(image, (r.x1, r.y1), (r.x2, r.y2), (0, 0, 255), 2)
    for y in segmentation.horizontal_separators:
        cv2.line(image, (r.x1, y), (r.x2, y), (0, 255, 0), 1)
    for x in segmentation.vertical_separators:
        cv2.line(image, (x, r.y1), (x, r.y2), (255, 0, 0), 1)

    for row in segmentation.rows:
        if label_every > 0 and row.index % label_every == 0:
            cv2.putText(
                image,
                f"r{row.index}",
                (row.bbox.x1 + 2, max(12, row.bbox.y1 + 11)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.32,
                (0, 0, 255),
                1,
                cv2.LINE_AA,
            )
        if draw_cells:
            for cell in row.cells:
                cv2.rectangle(
                    image,
                    (cell.bbox.x1, cell.bbox.y1),
                    (cell.bbox.x2, cell.bbox.y2),
                    (255, 200, 0),
                    1,
                )

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(output_path), image)


def refine_region_to_grid(
    image_path: str | Path,
    region: BBox,
    *,
    max_snap_ratio: float = 0.28,
) -> BBox:
    """Snap approximate supplier-template x boundaries to strong full-page table rules.

    Supplier profiles can be intentionally loose. Snapping only the left/right edges to nearby strong
    vertical rules avoids bleeding neighboring brands into OCR while keeping the profile robust to small
    template shifts. Y is deliberately preserved because section headers may not have full-width rules.
    """
    from .grid import profile_image

    profile = profile_image(image_path)
    candidates = profile.vertical_lines
    if not candidates:
        return region

    max_dist = max(8, int(region.width * max_snap_ratio))

    def snap(value: int) -> int:
        nearest = min(candidates, key=lambda x: abs(x - value))
        return int(nearest) if abs(nearest - value) <= max_dist else value

    x1, x2 = snap(region.x1), snap(region.x2)
    if x2 <= x1:
        return region
    return BBox(x1, region.y1, x2, region.y2)
