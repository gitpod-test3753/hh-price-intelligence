from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
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
    trim_borders: bool = False
    contrast_stretch: bool = False
    focus_ink: bool = False
    pad_px: int = 0
    x_margin_px: int = 0


@lru_cache(maxsize=16)
def _load_cached_bgr(path_str: str, mtime_ns: int) -> np.ndarray:
    img = cv2.imread(path_str, cv2.IMREAD_COLOR)
    if img is None:
        raise FileNotFoundError(path_str)
    img.setflags(write=False)
    return img


def load_region(image_path: str | Path, region: BBox | None = None) -> tuple[np.ndarray, tuple[int, int]]:
    """Load an image (or crop) as BGR plus source-space offset."""
    p = Path(image_path)
    if not p.exists():
        raise FileNotFoundError(image_path)
    img = _load_cached_bgr(str(p.resolve()), p.stat().st_mtime_ns)
    if region is None:
        return img.copy(), (0, 0)

    h, w = img.shape[:2]
    x1 = max(0, min(w, int(region.x1)))
    y1 = max(0, min(h, int(region.y1)))
    x2 = max(x1 + 1, min(w, int(region.x2)))
    y2 = max(y1 + 1, min(h, int(region.y2)))
    return img[y1:y2, x1:x2].copy(), (x1, y1)


def has_cell_ink(image_path: str | Path, region: BBox | None = None) -> bool:
    """Fast pure-NumPy check (<0.05ms) to avoid spawning OCR on blank table cells."""
    crop, _ = load_region(image_path, region)
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY) if crop.ndim == 3 else crop
    gray = trim_cell_borders(gray, x_margin_px=2)
    h, w = gray.shape
    if h > 4 and w > 6:
        gray = gray[1 : h - 1, 1 : w - 1]
    if gray.size < 12:
        return False
    lo, hi = np.percentile(gray, (5, 92))
    if hi - lo < 18:
        return False
    _, bw = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    ink = int((bw > 0).sum())
    return ink >= 5 and (bw > 0).mean() < 0.72


def _remove_grid(binary: np.ndarray) -> np.ndarray:
    """Remove long table rules while keeping compact glyph strokes."""
    inv = 255 - binary
    h, w = inv.shape[:2]
    hk = max(18, w // 18)
    vk = max(18, h // 18)
    horizontal = cv2.morphologyEx(inv, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (hk, 1)))
    vertical = cv2.morphologyEx(inv, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (1, vk)))
    lines = cv2.bitwise_or(horizontal, vertical)
    cleaned_inv = cv2.subtract(inv, lines)
    return 255 - cleaned_inv


def trim_cell_borders(gray: np.ndarray, *, x_margin_px: int = 0) -> np.ndarray:
    """Strip solid horizontal/vertical rule lines from the outer 1-2px edges of a cell crop."""
    h, w = gray.shape
    if h <= 5 or w <= 8:
        return gray
    _, bw = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    y1, y2 = 0, h
    while y1 < min(2, y2 - 4) and (bw[y1] > 0).mean() > 0.72:
        y1 += 1
    while y2 > max(y1 + 4, h - 2) and (bw[y2 - 1] > 0).mean() > 0.72:
        y2 -= 1
    x1 = min(max(0, x_margin_px), w // 4)
    x2 = max(x1 + 4, w - min(max(0, x_margin_px), w // 4))
    while x1 < min(x_margin_px + 3, x2 - 4) and (bw[y1:y2, x1] > 0).mean() > 0.68:
        x1 += 1
    while x2 > max(x1 + 4, w - x_margin_px - 3) and (bw[y1:y2, x2 - 1] > 0).mean() > 0.68:
        x2 -= 1
    return gray[y1:y2, x1:x2]


def focus_cell_ink(gray: np.ndarray, *, clear_outer_px: int = 1) -> np.ndarray:
    """Tightly crop to the foreground ink inside a cell, returning white canvas if empty."""
    h, w = gray.shape
    if h <= 4 or w <= 6:
        return gray
    work = gray.copy()
    if clear_outer_px > 0 and h > 2 * clear_outer_px + 4 and w > 2 * clear_outer_px + 4:
        work[:clear_outer_px, :] = 255
        work[-clear_outer_px:, :] = 255
        work[:, :clear_outer_px] = 255
        work[:, -clear_outer_px:] = 255
    lo, hi = np.percentile(work, (3, 92))
    if hi - lo < 16:
        return np.full((12, 24), 255, dtype=np.uint8)
    _, bw = cv2.threshold(work, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    ink_pixels = int((bw > 0).sum())
    if ink_pixels < 5 or (bw > 0).mean() > 0.75:
        return np.full((12, 24), 255, dtype=np.uint8)
    ys, xs = np.nonzero(bw)
    y1, y2 = max(0, int(ys.min()) - 1), min(h, int(ys.max()) + 2)
    x1, x2 = max(0, int(xs.min()) - 1), min(w, int(xs.max()) + 2)
    return work[y1:y2, x1:x2]


def preprocess_array(img: np.ndarray, options: PreprocessOptions) -> np.ndarray:
    work = img
    if options.grayscale and work.ndim == 3:
        work = cv2.cvtColor(work, cv2.COLOR_BGR2GRAY)
    if options.trim_borders:
        if work.ndim == 3:
            work = cv2.cvtColor(work, cv2.COLOR_BGR2GRAY)
        work = trim_cell_borders(work, x_margin_px=options.x_margin_px)
    if options.focus_ink:
        if work.ndim == 3:
            work = cv2.cvtColor(work, cv2.COLOR_BGR2GRAY)
        work = focus_cell_ink(work, clear_outer_px=1 if not options.trim_borders else 0)
    if options.contrast_stretch:
        if work.ndim == 3:
            work = cv2.cvtColor(work, cv2.COLOR_BGR2GRAY)
        lo, hi = np.percentile(work, (3, 94))
        if hi - lo >= 14:
            work = np.clip((work.astype(np.float32) - lo) * 255.0 / (hi - lo), 0, 255).astype(np.uint8)
        else:
            work = np.full_like(work, 255)
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
    if options.pad_px > 0:
        p = int(options.pad_px)
        fill = 255 if work.ndim == 2 else (255, 255, 255)
        work = cv2.copyMakeBorder(work, p, p, p + 4, p + 4, cv2.BORDER_CONSTANT, value=fill)
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
