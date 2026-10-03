from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

from hhpi.layout.models import BBox


@dataclass(frozen=True)
class PreprocessOptions:
    scale: float = 3.0
    grayscale: bool = True
    clahe: bool = True
    threshold: bool = False
    remove_grid_lines: bool = False
    invert: bool = False


def load_region(image_path: str | Path, region: BBox | None = None) -> tuple[np.ndarray, tuple[int, int]]:
    """Load an image (or crop) as BGR plus source-space offset."""
    img = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
    if img is None:
        raise FileNotFoundError(image_path)
    if region is None:
        return img, (0, 0)

    h, w = img.shape[:2]
    x1 = max(0, min(w, int(region.x1)))
    y1 = max(0, min(h, int(region.y1)))
    x2 = max(x1 + 1, min(w, int(region.x2)))
    y2 = max(y1 + 1, min(h, int(region.y2)))
    return img[y1:y2, x1:x2].copy(), (x1, y1)


def _remove_grid(binary: np.ndarray) -> np.ndarray:
    """Remove long table rules while keeping compact glyph strokes.

    Intended for OCR crops, not evidence storage. It is conservative: only long horizontal/vertical
    structures are removed.
    """
    inv = 255 - binary
    h, w = inv.shape[:2]
    hk = max(18, w // 18)
    vk = max(18, h // 18)
    horizontal = cv2.morphologyEx(inv, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (hk, 1)))
    vertical = cv2.morphologyEx(inv, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (1, vk)))
    lines = cv2.bitwise_or(horizontal, vertical)
    cleaned_inv = cv2.subtract(inv, lines)
    return 255 - cleaned_inv


def preprocess_array(img: np.ndarray, options: PreprocessOptions) -> np.ndarray:
    work = img
    if options.grayscale and work.ndim == 3:
        work = cv2.cvtColor(work, cv2.COLOR_BGR2GRAY)
    if options.clahe:
        if work.ndim == 3:
            work = cv2.cvtColor(work, cv2.COLOR_BGR2GRAY)
        work = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(work)
    if options.threshold:
        if work.ndim == 3:
            work = cv2.cvtColor(work, cv2.COLOR_BGR2GRAY)
        work = cv2.adaptiveThreshold(
            work, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 11
        )
    if options.remove_grid_lines:
        if work.ndim == 3:
            work = cv2.cvtColor(work, cv2.COLOR_BGR2GRAY)
        if not options.threshold:
            _, work = cv2.threshold(work, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        work = _remove_grid(work)
    if options.invert:
        work = 255 - work
    if options.scale and options.scale != 1.0:
        work = cv2.resize(
            work,
            None,
            fx=float(options.scale),
            fy=float(options.scale),
            interpolation=cv2.INTER_CUBIC,
        )
    return work


def preprocess_for_ocr(
    image_path: str | Path,
    *,
    region: BBox | None = None,
    options: PreprocessOptions | None = None,
) -> tuple[Image.Image, tuple[int, int], float]:
    options = options or PreprocessOptions()
    img, offset = load_region(image_path, region)
    work = preprocess_array(img, options)
    if work.ndim == 2:
        pil = Image.fromarray(work)
    else:
        pil = Image.fromarray(cv2.cvtColor(work, cv2.COLOR_BGR2RGB))
    return pil, offset, float(options.scale)
