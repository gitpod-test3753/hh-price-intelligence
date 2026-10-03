from __future__ import annotations

import re
import unicodedata

PERSIAN_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")
ARABIC_TO_PERSIAN = str.maketrans({"ي": "ی", "ك": "ک", "ة": "ه", "ۀ": "ه"})


def normalize_text(value: str) -> str:
    value = unicodedata.normalize("NFKC", value)
    value = value.translate(PERSIAN_DIGITS).translate(ARABIC_TO_PERSIAN)
    value = value.replace("–", "-").replace("—", "-")
    value = re.sub(r"\s+", " ", value).strip()
    return value


def compact_token(value: str) -> str:
    value = normalize_text(value).lower()
    return re.sub(r"[^0-9a-zآ-ی]+", "", value)
