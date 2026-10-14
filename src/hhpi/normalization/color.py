from __future__ import annotations

from rapidfuzz import fuzz, process

from .text import compact_token

COLOR_ALIASES: dict[str, set[str]] = {
    "black": {
        "black",
        "blk",
        "bk",
        "biack",
        "blak",
        "bleck",
        "slack",
        "glock",
        "alack",
        "aleck",
        "tgek",
        "مشکی",
        "مشكى",
        "مشک",
        "مشك",
        "هشکی",
        "هشک",
        "هشگی",
        "فشکی",
        "همشکی",
        "عشکی",
        "مکی",
        "مشق",
        "مشی",
        "مشگی",
        "مشکلی",
        "یکشم",
        "یكشم",
        "کشم",
    },
    "white": {
        "white",
        "wht",
        "whit",
        "starlight",
        "سفید",
        "سفيد",
        "سفبد",
        "سقید",
        "سفد",
    },
    "blue": {
        "blue",
        "blu",
        "biue",
        "bive",
        "bluc",
        "b1ue",
        "dice",
        "آبی",
        "ابي",
        "آبى",
        "ابى",
        "ابی روشن",
        "آبی روشن",
        "آبی یخی",
        "ای",
        "اى",
        "افی",
        "افى",
        "اب",
        "آب",
        "ایی",
        "آی",
        "یبا",
    },
    "green": {
        "green",
        "grn",
        "gre",
        "gren",
        "grecn",
        "olive",
        "lime",
        "mint",
        "سبز",
        "سهز",
        "سمز",
        "سبر",
        "سپز",
        "سیز",
        "سب",
        "سم",
        "سز",
        "مرو",
        "مب",
        "زبس",
    },
    "gray": {
        "gray",
        "grey",
        "gry",
        "grav",
        "grev",
        "graphite",
        "titan",
        "titanium",
        "گری",
        "گرى",
        "کری",
        "خاکستری",
        "خاکستر",
        "خاكستري",
        "تیتانیوم",
        "تیتان",
    },
    "silver": {
        "silver",
        "slv",
        "sliver",
        "سیلور",
        "سلور",
        "نقره ای",
        "نقرهای",
        "نقره",
    },
    "gold": {
        "gold",
        "gld",
        "goid",
        "desert",
        "گلد",
        "گند",
        "طلایی",
        "طلائى",
        "طلائی",
        "طلاپی",
        "طلای",
        "طلا",
        "کرم",
        "صحرایی",
    },
    "purple": {
        "purple",
        "prp",
        "purp",
        "purpie",
        "purole",
        "pur",
        "violet",
        "lilac",
        "lavender",
        "بنفش",
        "پنفش",
        "بتفش",
        "بتفقش",
        "پتقش",
        "پخقش",
        "پمشش",
        "بفش",
        "بنقش",
        "بنفس",
        "فش",
        "یاسی",
        "یاس",
        "پاسی",
        "شفنب",
    },
    "pink": {
        "pink",
        "pnk",
        "rosegold",
        "rose gold",
        "roseote",
        "صورتی",
        "صورت",
        "رزگلد",
    },
    "orange": {
        "orange",
        "org",
        "نارنجی",
        "نارنج",
        "تارنجی",
        "تارنج",
    },
    "red": {
        "red",
        "burgundy",
        "قرمز",
    },
    "yellow": {
        "yellow",
        "ylw",
        "زرد",
        "ررد",
        "درز",
    },
    "brown": {
        "brown",
        "3rown",
        "قهوه ای",
        "قهوهای",
    },
}

_LOOKUP = {compact_token(v): canonical for canonical, vals in COLOR_ALIASES.items() for v in vals}


def is_known_color(value: str | None) -> bool:
    if not value:
        return False
    return resolve_known_color(value) is not None


def resolve_known_color(value: str | None) -> str | None:
    if not value:
        return None
    token = compact_token(value)
    if not token:
        return None
    if token in _LOOKUP:
        return _LOOKUP[token]
    rev = token[::-1]
    if rev in _LOOKUP:
        return _LOOKUP[rev]
    # Check individual whitespace-separated words in case OCR attached a border symbol or noise word.
    for part in value.split():
        pt = compact_token(part)
        if pt in _LOOKUP:
            return _LOOKUP[pt]
        if pt[::-1] in _LOOKUP:
            return _LOOKUP[pt[::-1]]
    if len(token) >= 3:
        match = process.extractOne(token, _LOOKUP.keys(), scorer=fuzz.ratio, score_cutoff=80.0)
        if match:
            return _LOOKUP[match[0]]
    return None


def normalize_color(value: str | None) -> str | None:
    if not value:
        return None
    known = resolve_known_color(value)
    if known is not None:
        return known
    return normalize_unknown(value)


def normalize_unknown(value: str) -> str:
    return normalize_display(value)


def normalize_display(value: str) -> str:
    return " ".join(value.strip().split())
