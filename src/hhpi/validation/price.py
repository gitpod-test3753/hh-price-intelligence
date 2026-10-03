from __future__ import annotations

from dataclasses import dataclass
from statistics import median


@dataclass(frozen=True)
class PriceValidation:
    suspicious: bool
    reasons: tuple[str, ...]
    reference_median: int | None = None
    deviation_ratio: float | None = None


def validate_price(
    current_toman: int | None,
    *,
    same_supplier_history: list[int] | None = None,
    cross_supplier_current: list[int] | None = None,
    max_history_deviation: float = 0.35,
    max_market_deviation: float = 0.40,
) -> PriceValidation:
    """Flag suspicious OCR prices without ever replacing the observed value."""
    if current_toman is None or current_toman <= 0:
        return PriceValidation(True, ("missing_or_nonpositive_price",))

    reasons: list[str] = []
    reference_values: list[int] = []

    history = [v for v in (same_supplier_history or []) if v > 0]
    if history:
        ref = int(median(history[-7:]))
        reference_values.append(ref)
        deviation = abs(current_toman - ref) / ref
        if deviation > max_history_deviation:
            reasons.append(f"history_deviation:{deviation:.3f}")

    market = [v for v in (cross_supplier_current or []) if v > 0]
    if market:
        ref = int(median(market))
        reference_values.append(ref)
        deviation = abs(current_toman - ref) / ref
        if deviation > max_market_deviation:
            reasons.append(f"market_deviation:{deviation:.3f}")

    reference = int(median(reference_values)) if reference_values else None
    deviation_ratio = (
        round(abs(current_toman - reference) / reference, 4) if reference and reference > 0 else None
    )
    return PriceValidation(bool(reasons), tuple(reasons), reference, deviation_ratio)
