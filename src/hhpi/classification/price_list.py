from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from hhpi.layout.grid import profile_image


@dataclass(frozen=True)
class ClassificationResult:
    label: str
    confidence: float
    reasons: tuple[str, ...]


class StructuralPriceListClassifier:
    """Cheap OCR-free triage classifier.

    This is not the final semantic classifier. It is intentionally conservative and exists to reject
    obvious non-list images before expensive OCR/VLM work. Borderline cases should be escalated.
    """

    def __init__(self, *, positive_threshold: float = 0.72, reject_threshold: float = 0.40) -> None:
        self.positive_threshold = positive_threshold
        self.reject_threshold = reject_threshold

    def classify(self, path: str | Path) -> ClassificationResult:
        profile = profile_image(path)
        score = profile.table_likelihood
        reasons = [
            f"table_likelihood={score:.3f}",
            f"horizontal_lines={len(profile.horizontal_lines)}",
            f"vertical_lines={len(profile.vertical_lines)}",
            f"ink_ratio={profile.ink_ratio:.3f}",
        ]
        if score >= self.positive_threshold:
            return ClassificationResult("price_list", score, tuple(reasons))
        if score <= self.reject_threshold:
            return ClassificationResult("not_price_list", 1.0 - score, tuple(reasons))
        return ClassificationResult("uncertain", 1.0 - abs(0.5 - score), tuple(reasons))
