from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

from .models import BBox, StructuralProfile


def _read(path: str | Path) -> np.ndarray:
    image = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError(f"Unable to read image: {path}")
    return image


def _binary_ink(image: np.ndarray) -> np.ndarray:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # Inverted binary: text/grid lines become 255. Otsu adapts across colored sheets.
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    return binary


def _line_masks(binary: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    h, w = binary.shape
    # Use scale-relative kernels. These capture table rules without requiring OCR.
    h_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (max(12, w // 28), 1))
    v_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, max(12, h // 35)))
    horizontal = cv2.morphologyEx(binary, cv2.MORPH_OPEN, h_kernel)
    vertical = cv2.morphologyEx(binary, cv2.MORPH_OPEN, v_kernel)
    return horizontal, vertical


def _peaks(mask: np.ndarray, axis: int, threshold_ratio: float) -> tuple[int, ...]:
    # axis=1 -> per-row projection, axis=0 -> per-column projection
    projection = (mask > 0).sum(axis=axis)
    full = mask.shape[1] if axis == 1 else mask.shape[0]
    candidates = np.flatnonzero(projection >= max(2, full * threshold_ratio))
    if not len(candidates):
        return ()

    # Merge adjacent pixels belonging to the same physical rule into one center coordinate.
    groups: list[list[int]] = [[int(candidates[0])]]
    for value in candidates[1:]:
        value = int(value)
        if value <= groups[-1][-1] + 2:
            groups[-1].append(value)
        else:
            groups.append([value])
    return tuple(int(round(sum(g) / len(g))) for g in groups)


def profile_image(path: str | Path) -> StructuralProfile:
    image = _read(path)
    binary = _binary_ink(image)
    horizontal, vertical = _line_masks(binary)
    h, w = binary.shape

    h_lines = _peaks(horizontal, axis=1, threshold_ratio=0.18)
    v_lines = _peaks(vertical, axis=0, threshold_ratio=0.12)
    ink_ratio = float(np.count_nonzero(binary) / binary.size)
    h_ratio = float(np.count_nonzero(horizontal) / horizontal.size)
    v_ratio = float(np.count_nonzero(vertical) / vertical.size)

    # Structural score, intentionally OCR-free. It is a triage hint, never a final classifier.
    line_count_score = min(1.0, (len(h_lines) / 35.0) + (len(v_lines) / 18.0))
    line_pixel_score = min(1.0, (h_ratio + v_ratio) * 16.0)
    density_score = min(1.0, max(0.0, (ink_ratio - 0.05) / 0.25))
    likelihood = round(0.50 * line_count_score + 0.35 * line_pixel_score + 0.15 * density_score, 4)

    return StructuralProfile(
        width=w,
        height=h,
        aspect_ratio=round(w / h, 5),
        ink_ratio=round(ink_ratio, 6),
        horizontal_line_ratio=round(h_ratio, 6),
        vertical_line_ratio=round(v_ratio, 6),
        horizontal_lines=h_lines,
        vertical_lines=v_lines,
        table_likelihood=likelihood,
    )


def find_table_regions(path: str | Path, min_area_ratio: float = 0.015) -> list[BBox]:
    """Find grid-dense connected regions.

    This intentionally does not claim that every returned region is a semantic table. It produces
    candidate regions for OCR/table engines and supports supplier-template fingerprinting.
    """
    image = _read(path)
    binary = _binary_ink(image)
    horizontal, vertical = _line_masks(binary)
    grid = cv2.bitwise_or(horizontal, vertical)

    # Close small gaps so adjacent cells form a component while keeping separate table sections apart.
    h, w = grid.shape
    kernel = cv2.getStructuringElement(
        cv2.MORPH_RECT,
        (max(3, w // 250), max(3, h // 250)),
    )
    connected = cv2.morphologyEx(grid, cv2.MORPH_CLOSE, kernel, iterations=2)
    contours, _ = cv2.findContours(connected, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    min_area = w * h * min_area_ratio
    boxes: list[BBox] = []
    for contour in contours:
        x, y, bw, bh = cv2.boundingRect(contour)
        if bw * bh < min_area:
            continue
        if bw < w * 0.08 or bh < h * 0.05:
            continue
        boxes.append(BBox(x, y, x + bw, y + bh))

    boxes.sort(key=lambda b: (b.y1, b.x1))
    return boxes


def render_overlay(path: str | Path, output: str | Path) -> list[BBox]:
    image = _read(path)
    boxes = find_table_regions(path)
    profile = profile_image(path)

    for y in profile.horizontal_lines:
        cv2.line(image, (0, y), (image.shape[1] - 1, y), (0, 255, 0), 1)
    for x in profile.vertical_lines:
        cv2.line(image, (x, 0), (x, image.shape[0] - 1), (255, 0, 0), 1)
    for idx, box in enumerate(boxes, start=1):
        cv2.rectangle(image, (box.x1, box.y1), (box.x2, box.y2), (0, 0, 255), 2)
        cv2.putText(
            image,
            f"R{idx}",
            (box.x1 + 4, max(14, box.y1 + 16)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            (0, 0, 255),
            1,
            cv2.LINE_AA,
        )
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(output), image)
    return boxes
