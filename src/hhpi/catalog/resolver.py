from __future__ import annotations

from dataclasses import dataclass
import re

from rapidfuzz import fuzz, process

from hhpi.normalization.text import compact_token, normalize_text


@dataclass(frozen=True)
class CatalogItem:
    canonical_id: str
    brand: str
    model: str
    aliases: tuple[str, ...] = ()


@dataclass(frozen=True)
class Resolution:
    canonical_id: str | None
    score: float
    matched_alias: str | None
    method: str
    brand: str | None = None
    model_canonical: str | None = None


DEFAULT_CATALOG_ITEMS: tuple[CatalogItem, ...] = (
    # Xiaomi Redmi Note 15 series
    CatalogItem(
        "xiaomi:redmi_note_15_pro_plus",
        "Xiaomi",
        "Redmi Note 15 Pro+",
        ("Note 15 Pro Plus", "Note 15 Pro+", "Redmi Note 15 Pro Plus", "نوت 15 پرو پلاس"),
    ),
    CatalogItem(
        "xiaomi:redmi_note_15_pro",
        "Xiaomi",
        "Redmi Note 15 Pro",
        ("Note 15 Pro", "Note 15Pro", "Redmi Note 15 Pro", "نوت 15 پرو"),
    ),
    CatalogItem(
        "xiaomi:redmi_note_15",
        "Xiaomi",
        "Redmi Note 15",
        ("Note 15", "Note15", "Redmi Note 15", "ردمی نوت 15", "N15"),
    ),
    # Xiaomi Redmi Note 14 series
    CatalogItem(
        "xiaomi:redmi_note_14_pro_plus",
        "Xiaomi",
        "Redmi Note 14 Pro+",
        ("Note 14 Pro Plus", "Note 14 Pro+", "Note14Pro+", "Redmi Note 14 Pro Plus"),
    ),
    CatalogItem(
        "xiaomi:redmi_note_14_pro",
        "Xiaomi",
        "Redmi Note 14 Pro",
        ("Note 14 Pro", "Note14Pro", "Redmi Note 14 Pro"),
    ),
    CatalogItem(
        "xiaomi:redmi_note_14s",
        "Xiaomi",
        "Redmi Note 14S",
        ("Note 14S", "Note14S", "Redmi Note 14S"),
    ),
    CatalogItem(
        "xiaomi:redmi_note_14",
        "Xiaomi",
        "Redmi Note 14",
        ("Note 14", "Note14", "Redmi Note 14"),
    ),
    # Xiaomi Redmi numbered & A/C series
    CatalogItem(
        "xiaomi:redmi_15c",
        "Xiaomi",
        "Redmi 15C",
        ("Redmi 15C", "Redmi15C", "15C"),
    ),
    CatalogItem(
        "xiaomi:redmi_15",
        "Xiaomi",
        "Redmi 15",
        ("Redmi 15", "Redmi15"),
    ),
    CatalogItem(
        "xiaomi:redmi_14c",
        "Xiaomi",
        "Redmi 14C",
        ("Redmi 14C", "Redmi14C", "14C"),
    ),
    CatalogItem(
        "xiaomi:redmi_13x",
        "Xiaomi",
        "Redmi 13X",
        ("Redmi 13X", "Redmi13X", "13X"),
    ),
    CatalogItem(
        "xiaomi:redmi_13c",
        "Xiaomi",
        "Redmi 13C",
        ("Redmi 13C", "Redmi13C", "13C"),
    ),
    CatalogItem(
        "xiaomi:redmi_13",
        "Xiaomi",
        "Redmi 13",
        ("Redmi 13", "Redmi13"),
    ),
    CatalogItem(
        "xiaomi:redmi_a7_pro",
        "Xiaomi",
        "Redmi A7 Pro",
        ("Redmi A7 Pro", "A7 Pro", "RedmiA7Pro"),
    ),
    CatalogItem(
        "xiaomi:redmi_a5",
        "Xiaomi",
        "Redmi A5",
        ("Redmi A5", "RedmiA5", "A5"),
    ),
    CatalogItem(
        "xiaomi:redmi_a3",
        "Xiaomi",
        "Redmi A3",
        ("Redmi A3", "RedmiA3", "A3"),
    ),
    # Xiaomi T-series & Flagships
    CatalogItem(
        "xiaomi:17_pro_max",
        "Xiaomi",
        "Xiaomi 17 Pro Max",
        ("Note 17 Pro Max", "17 Pro Max", "17T Pro"),
    ),
    CatalogItem(
        "xiaomi:15t_pro",
        "Xiaomi",
        "Xiaomi 15T Pro",
        ("15T Pro", "Xiaomi 15T Pro"),
    ),
    CatalogItem(
        "xiaomi:15t",
        "Xiaomi",
        "Xiaomi 15T",
        ("15T", "Xiaomi 15T"),
    ),
    CatalogItem(
        "xiaomi:14t_pro",
        "Xiaomi",
        "Xiaomi 14T Pro",
        ("14T Pro", "Xiaomi 14T Pro"),
    ),
    CatalogItem(
        "xiaomi:14t",
        "Xiaomi",
        "Xiaomi 14T",
        ("14T", "Xiaomi 14T"),
    ),
    # Poco series
    CatalogItem(
        "xiaomi:poco_x8_pro",
        "Xiaomi",
        "Poco X8 Pro",
        ("Poco X8 Pro", "X8 Pro", "POCOX8PRO"),
    ),
    CatalogItem(
        "xiaomi:poco_x7_pro",
        "Xiaomi",
        "Poco X7 Pro",
        ("Poco X7 Pro", "X7 Pro", "POCOX7PRO"),
    ),
    CatalogItem(
        "xiaomi:poco_f6_pro",
        "Xiaomi",
        "Poco F6 Pro",
        ("Poco F6 Pro", "F6 Pro"),
    ),
    CatalogItem(
        "xiaomi:poco_f6",
        "Xiaomi",
        "Poco F6",
        ("Poco F6", "F6"),
    ),
    CatalogItem(
        "xiaomi:poco_m8_pro",
        "Xiaomi",
        "Poco M8 Pro",
        ("Poco M8 Pro", "M8 Pro"),
    ),
    CatalogItem(
        "xiaomi:poco_m7_pro",
        "Xiaomi",
        "Poco M7 Pro",
        ("Poco M7 Pro", "M7 Pro"),
    ),
    CatalogItem(
        "xiaomi:poco_m7",
        "Xiaomi",
        "Poco M7",
        ("Poco M7", "M7"),
    ),
    CatalogItem(
        "xiaomi:poco_c85",
        "Xiaomi",
        "Poco C85",
        ("Poco C85", "POCOC85", "C85"),
    ),
    CatalogItem(
        "xiaomi:poco_c81",
        "Xiaomi",
        "Poco C81",
        ("Poco C81", "POCOC81", "C81"),
    ),
    CatalogItem(
        "xiaomi:poco_c75",
        "Xiaomi",
        "Poco C75",
        ("Poco C75", "POCOC75", "C75", "C75 4G"),
    ),
    CatalogItem(
        "xiaomi:poco_c71",
        "Xiaomi",
        "Poco C71",
        ("Poco C71", "POCOC71", "C71"),
    ),
    # Xiaomi Tablets
    CatalogItem(
        "xiaomi:poco_pad_m1",
        "Xiaomi",
        "Poco Pad M1",
        ("Poco Pad M1", "POCOPADM1"),
    ),
    CatalogItem(
        "xiaomi:redmi_pad_2_pro",
        "Xiaomi",
        "Redmi Pad 2 Pro",
        ("Xiaomi Redmi Pad 2 Pro", "Redmi Pad 2 Pro", "Xiaomi Redmi Pad Pro"),
    ),
    CatalogItem(
        "xiaomi:redmi_pad_2",
        "Xiaomi",
        "Redmi Pad 2",
        ("Xiaomi Redmi Pad 2", "Redmi Pad 2"),
    ),
    CatalogItem(
        "xiaomi:pad_7",
        "Xiaomi",
        "Xiaomi Pad 7",
        ("Xiaomi Pad 7", "Pad 7"),
    ),
    # Realme series (present at bottom of 15276 Xiaomi panel)
    CatalogItem(
        "realme:12_plus",
        "Realme",
        "Realme 12+",
        ("12 Plus", "Realme 12 Plus"),
    ),
    CatalogItem(
        "realme:note_50",
        "Realme",
        "Realme Note 50",
        ("Note 50", "Realme Note 50"),
    ),
    CatalogItem(
        "realme:c75x",
        "Realme",
        "Realme C75x",
        ("C75X", "Realme C75X"),
    ),
    CatalogItem(
        "realme:c61",
        "Realme",
        "Realme C61",
        ("C61", "Realme C61"),
    ),
)


def clean_model_for_catalog(raw: str) -> str:
    """Strip memory/network suffixes and repair common OCR border/character confusions."""
    s = normalize_text(raw)
    # Remove leading border vertical-bar artifacts like `INOTE`, `IREDMI`, `|Note`, `[Poco`
    s = re.sub(r"^[\|\[\(\{\/\\!1I]+(?=[A-Za-z]{3,})", "", s).strip()
    # Repair common OCR model token confusions
    s = re.sub(r"\b(?:Mote|Nete|Nate|Vote|Unte|Unto|Mate)\b", "Note", s, flags=re.IGNORECASE)
    s = re.sub(r"\b(?:Ream|Readmi|Feteni)\b", "Redmi", s, flags=re.IGNORECASE)
    s = re.sub(r"\bPra\b", "Pro", s, flags=re.IGNORECASE)
    s = re.sub(r"\bolis\b|\boli\b|\bpeophus\b", "Plus", s, flags=re.IGNORECASE)
    s = re.sub(r"(?i)\b(NOTE\s*1)[sS]", r"\g<1>5", s)
    s = re.sub(r"(?i)\b(REDMI\s*1)[sS]", r"\g<1>5", s)
    s = re.sub(r"(?i)\b(REDMI\s*A)[sS]", r"\g<1>5", s)
    s = re.sub(r"(?i)\b(POCO\s*X)[bBsS]", r"\g<1>8", s)
    s = re.sub(r"(?i)\b(POCO\s*C)(?:8[sS]|S[sS5]|ES)", r"\g<1>85", s)
    # Strip memory pairs (e.g., 512/12, 256/8, 8/256, 12/512, 12512) and glued 4G/5G/NFC/WIFI tokens
    s = re.sub(r"(?i)\b(?:512|256|128|64|32|16|12|8|6|4|3|2)\s*[/\\-]\s*\d{1,4}(?:[45][gG])?\b", " ", s)
    s = re.sub(r"(?i)(?:512|256|128|64)\s*[/\\-]\s*\d{1,4}(?:[45][gG])?", " ", s)
    s = re.sub(r"(?i)\b(?:16|12|8|6|4)(?:512|256|128|592|612)\b", " ", s)
    s = re.sub(r"(?i)\b(?:[45][gG]|nfc|wifi|ch|global|گلوبال|شرکتی)\b", " ", s)
    # Remove trailing non-alphanumeric noise tokens
    s = re.sub(r"[^A-Za-z0-9آ-ی\+]+$", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


class CatalogResolver:
    def __init__(self, items: list[CatalogItem] | tuple[CatalogItem, ...]) -> None:
        self.items = list(items)
        self._aliases: dict[str, CatalogItem] = {}
        self._display_by_key: dict[str, str] = {}
        for item in self.items:
            values = (item.model, *item.aliases)
            for value in values:
                key = compact_token(value)
                self._aliases[key] = item
                self._display_by_key[key] = normalize_text(value)

    def resolve(self, raw: str, *, threshold: float = 84.0) -> Resolution:
        for candidate_raw in (raw, clean_model_for_catalog(raw)):
            key = compact_token(candidate_raw)
            if not key:
                continue
            if key in self._aliases:
                item = self._aliases[key]
                return Resolution(
                    item.canonical_id,
                    100.0,
                    self._display_by_key[key],
                    "exact_alias",
                    brand=item.brand,
                    model_canonical=item.model,
                )

        cleaned_key = compact_token(clean_model_for_catalog(raw)) or compact_token(raw)
        if not cleaned_key:
            return Resolution(None, 0.0, None, "unresolved")

        match = process.extractOne(
            cleaned_key,
            self._aliases.keys(),
            scorer=fuzz.WRatio,
            score_cutoff=threshold,
        )
        if not match:
            return Resolution(None, 0.0, None, "unresolved")
        alias_key, score, _ = match
        item = self._aliases[alias_key]
        return Resolution(
            item.canonical_id,
            round(float(score), 2),
            self._display_by_key[alias_key],
            "fuzzy_alias",
            brand=item.brand,
            model_canonical=item.model,
        )


def default_catalog_resolver() -> CatalogResolver:
    return CatalogResolver(DEFAULT_CATALOG_ITEMS)
