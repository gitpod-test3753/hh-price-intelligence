from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from pathlib import Path

from .grid import profile_image
from .models import StructuralProfile


@dataclass(frozen=True)
class TemplateFingerprint:
    bins: tuple[float, ...]
    aspect_ratio: float
    ink_ratio: float


def _histogram(coords: tuple[int, ...], extent: int, bins: int) -> list[float]:
    values = [0.0] * bins
    if extent <= 0:
        return values
    for coord in coords:
        idx = min(bins - 1, int((coord / extent) * bins))
        values[idx] += 1.0
    total = sum(values)
    return [v / total for v in values] if total else values


def fingerprint_profile(profile: StructuralProfile, *, bins: int = 32) -> TemplateFingerprint:
    h_hist = _histogram(profile.horizontal_lines, profile.height, bins)
    v_hist = _histogram(profile.vertical_lines, profile.width, bins)
    return TemplateFingerprint(
        bins=tuple(h_hist + v_hist),
        aspect_ratio=profile.aspect_ratio,
        ink_ratio=profile.ink_ratio,
    )


def fingerprint_image(path: str | Path, *, bins: int = 32) -> TemplateFingerprint:
    return fingerprint_profile(profile_image(path), bins=bins)


def similarity(a: TemplateFingerprint, b: TemplateFingerprint) -> float:
    dot = sum(x * y for x, y in zip(a.bins, b.bins))
    na = sqrt(sum(x * x for x in a.bins))
    nb = sqrt(sum(y * y for y in b.bins))
    cosine = dot / (na * nb) if na and nb else 0.0

    aspect_penalty = min(1.0, abs(a.aspect_ratio - b.aspect_ratio) / max(a.aspect_ratio, b.aspect_ratio, 1e-9))
    ink_penalty = min(1.0, abs(a.ink_ratio - b.ink_ratio) / max(a.ink_ratio, b.ink_ratio, 1e-9))
    score = cosine * (1.0 - 0.20 * aspect_penalty) * (1.0 - 0.10 * ink_penalty)
    return round(max(0.0, min(1.0, score)), 4)
