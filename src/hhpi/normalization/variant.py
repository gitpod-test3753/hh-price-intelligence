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

# Common OCR digit confusions in supplier sheets (e.g., 256 -> 266/258/286, 512 -> 612/592, 128 -> 178).
_STORAGE_OCR_REPAIRS: dict[str, int] = {
    "266": 256,
    "258": 256,
    "286": 256,
    "250": 256,
    "255": 256,
    "612": 512,
    "592": 512,
    "517": 512,
    "812": 512,
    "178": 128,
    "126": 128,
}

# Physically plausible (storage_gb, ram_gb) pairs in wholesale mobile sheets.
_VALID_PAIRS: set[tuple[int, int]] = {
    (32, 2),
    (32, 3),
    (32, 4),
    (64, 2),
    (64, 3),
    (64, 4),
    (64, 6),
    (128, 3),
    (128, 4),
    (128, 6),
    (128, 8),
    (128, 12),
    (256, 4),
    (256, 6),
    (256, 8),
    (256, 12),
    (256, 16),
    (512, 8),
    (512, 12),
    (512, 16),
    (512, 24),
    (1024, 12),
    (1024, 16),
    (1024, 24),
    (2048, 16),
    (2048, 24),
    (2048, 32),
}


def _suffix_candidate(digits: str, candidates: tuple[int, ...]) -> int | None:
    """Return a valid capacity that is a suffix of an OCR-glued digit run."""
    hits = [c for c in candidates if digits.endswith(str(c))]
    if hits:
        return max(hits, key=lambda c: len(str(c)))
    for bad, good in _STORAGE_OCR_REPAIRS.items():
        if good in candidates and digits.endswith(bad):
            return good
    return None


def _prefix_ram_candidate(digits: str) -> int | None:
    """Recover RAM when OCR glued 4G/5G (as 46/56/40/50) or a trailing noise digit to RAM.

    Examples:
    - `256/846` -> right=`846` = RAM `8` + `4G` (misread as `46`)
    - `512/1256` -> right=`1256` = RAM `12` + `5G` (misread as `56`)
    - `512/122` -> right=`122` = RAM `12` + trailing noise `2`
    """
    if digits in {str(c) for c in COMMON_RAM_GB}:
        return int(digits)
    # Check <ram>(46|56|40|50) from glued 4G/5G
    m_net = re.fullmatch(r"(16|12|8|6|4|3|2)(?:46|56|40|50)", digits)
    if m_net:
        return int(m_net.group(1))
    # Check <ram> followed by single noise digit (e.g. 122 -> 12)
    m_noise = re.fullmatch(r"(16|12|8|6|4)\d", digits)
    if m_noise:
        return int(m_noise.group(1))
    return _suffix_candidate(digits, COMMON_RAM_GB)


def parse_memory_variant(text: str) -> MemoryVariant:
    s = normalize_text(text).lower().replace("gb", "")
    # Normalize 1TB / 1T in memory pairs like `12-1T` or `1T/16` to `1024`.
    s = re.sub(r"(?<=[/\\\s-])1\s*tb?(?=$|[^a-z0-9])", "1024", s)
    s = re.sub(r"(?:^|(?<=\s))1\s*tb?(?=[/\\-])", "1024", s)
    # Repair OCR where `8/` was misread as `w` or `a` right before `256` or `128` (e.g. `Note 15 W256`).
    s = re.sub(r"(?<=\s)[wa](?=256|128\b)", "8/", s)

    for match in re.finditer(r"(\d{1,6})\s*[/\\-]\s*(\d{1,4})", s):
        left, right = match.group(1), match.group(2)

        left_storage = _suffix_candidate(left, COMMON_STORAGE_GB)
        right_ram = _prefix_ram_candidate(right)
        if left_storage is not None and right_ram is not None and (left_storage, right_ram) in _VALID_PAIRS:
            return MemoryVariant(ram_gb=right_ram, storage_gb=left_storage)

        left_ram = _suffix_candidate(left, COMMON_RAM_GB)
        right_storage = _suffix_candidate(right, COMMON_STORAGE_GB)
        if right_storage is None and len(right) >= 3:
            right_storage = _STORAGE_OCR_REPAIRS.get(right[:3])
        if left_ram is not None and right_storage is not None and (right_storage, left_ram) in _VALID_PAIRS:
            return MemoryVariant(ram_gb=left_ram, storage_gb=right_storage)

        # Fallback without strict pair filter if capacities are individually valid
        if left_storage is not None and right_ram is not None:
            return MemoryVariant(ram_gb=right_ram, storage_gb=left_storage)
        if left_ram is not None and right_storage is not None:
            return MemoryVariant(ram_gb=left_ram, storage_gb=right_storage)

    # Fallback for OCR that dropped the slash between RAM and 3-digit storage (e.g. `12512` or `8256`).
    for match in re.finditer(r"(?<!\d)(16|12|8|6|4)(512|256|128|592|612)(?!\d)", s):
        ram = int(match.group(1))
        raw_st = match.group(2)
        storage = _STORAGE_OCR_REPAIRS.get(raw_st, int(raw_st))
        if (storage, ram) in _VALID_PAIRS:
            return MemoryVariant(ram_gb=ram, storage_gb=storage)

    return MemoryVariant(None, None)
