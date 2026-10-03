from __future__ import annotations

import re
from dataclasses import dataclass

from .text import normalize_text


@dataclass(frozen=True)
class MemoryVariant:
    ram_gb: int | None
    storage_gb: int | None


# Keep the catalog conservative. Unknown capacities should remain unresolved rather than be guessed.
COMMON_RAM_GB = (2, 3, 4, 6, 8, 12, 16, 24, 32)
COMMON_STORAGE_GB = (32, 64, 128, 256, 512, 1024, 2048)


def _suffix_candidate(digits: str, candidates: tuple[int, ...]) -> int | None:
    """Return a valid capacity that is a suffix of an OCR-glued digit run.

    Example: model text `C7164/4` contains a model digit immediately before storage. The storage token is
    still recoverable as the suffix `64`, while treating `7164` as storage would be a destructive guess.
    """
    hits = [c for c in candidates if digits.endswith(str(c))]
    return max(hits, key=lambda c: len(str(c))) if hits else None


def parse_memory_variant(text: str) -> MemoryVariant:
    s = normalize_text(text).lower().replace("gb", "")

    # Search every slash/hyphen pair, including pairs glued to model/network tokens. Validate against a
    # conservative capacity catalog and prefer the longest plausible suffix on each side.
    for match in re.finditer(r"(\d{1,6})\s*[/\\-]\s*(\d{1,4})", s):
        left, right = match.group(1), match.group(2)

        left_storage = _suffix_candidate(left, COMMON_STORAGE_GB)
        right_ram = _suffix_candidate(right, COMMON_RAM_GB)
        if left_storage is not None and right_ram is not None:
            return MemoryVariant(ram_gb=right_ram, storage_gb=left_storage)

        left_ram = _suffix_candidate(left, COMMON_RAM_GB)
        right_storage = _suffix_candidate(right, COMMON_STORAGE_GB)
        if left_ram is not None and right_storage is not None:
            return MemoryVariant(ram_gb=left_ram, storage_gb=right_storage)

    return MemoryVariant(None, None)
