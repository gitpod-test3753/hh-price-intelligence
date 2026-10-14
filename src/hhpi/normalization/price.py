from __future__ import annotations

import re

from hhpi.domain.models import Availability, PriceBasis, PriceValue
from .text import normalize_text

_MARKERS = {
    "call": Availability.CALL,
    "تماس": Availability.CALL,
    "soon": Availability.SOON,
    "بزودی": Availability.SOON,
    "به زودی": Availability.SOON,
    "***": Availability.UNPRICED,
    "****": Availability.UNPRICED,
    "-": Availability.UNPRICED,
    "--": Availability.UNPRICED,
    "---": Availability.UNPRICED,
    "----": Availability.UNPRICED,
    "بدون کد": Availability.UNPRICED,
    "شرکتی": Availability.UNPRICED,
}


def _expand_market_range(left: int, right: int) -> tuple[int, int]:
    """Expand supplier shorthand like `149000-150` to `149000-150000`."""
    if left >= 10_000 and 0 < right < 1_000:
        right *= 1_000
    return left, right


def parse_price(
    raw: str,
    scale_toman: int = 1000,
    *,
    basis: PriceBasis | None = None,
    expand_market_shorthand: bool = True,
) -> PriceValue:
    text = normalize_text(raw).strip().lower()
    if text in _MARKERS or re.fullmatch(r"[\*\-\.]{2,}", text):
        marker = _MARKERS.get(text, Availability.UNPRICED)
        return PriceValue(
            raw=raw,
            availability=marker,
            basis=basis or PriceBasis.UNKNOWN,
        )

    cleaned = text.replace(",", "").replace("٬", "")
    nums = [int(x) for x in re.findall(r"\d+", cleaned)]
    if not nums:
        return PriceValue(raw=raw, availability=Availability.UNKNOWN, basis=basis or PriceBasis.UNKNOWN)

    is_range = len(nums) >= 2 and ("-" in cleaned or "تا" in cleaned)
    if is_range:
        low, high = nums[0], nums[1]
        if expand_market_shorthand:
            low, high = _expand_market_range(low, high)
        low, high = low * scale_toman, high * scale_toman
        if low > high:
            low, high = high, low
        return PriceValue(
            raw=raw,
            availability=Availability.AVAILABLE,
            basis=basis or PriceBasis.RANGE,
            min_toman=low,
            max_toman=high,
        )

    return PriceValue(
        raw=raw,
        availability=Availability.AVAILABLE,
        basis=basis or PriceBasis.SINGLE,
        normalized_toman=nums[0] * scale_toman,
    )
