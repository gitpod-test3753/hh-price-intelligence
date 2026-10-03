from __future__ import annotations

from .text import compact_token

COLOR_ALIASES = {
    "black": {"black", "blk", "bk", "مشکی", "مشكى"},
    "white": {"white", "wht", "سفید", "سفيد"},
    "blue": {"blue", "آبی", "ابي", "آبى"},
    "green": {"green", "سبز"},
    "gray": {"gray", "grey", "گری", "خاکستری"},
    "silver": {"silver", "سیلور", "نقره ای", "نقرهای"},
    "gold": {"gold", "گلد", "طلایی", "طلائى"},
    "purple": {"purple", "بنفش"},
    "pink": {"pink", "صورتی"},
    "orange": {"orange", "نارنجی"},
    "red": {"red", "قرمز"},
}

_LOOKUP = {compact_token(v): canonical for canonical, vals in COLOR_ALIASES.items() for v in vals}


def normalize_color(value: str | None) -> str | None:
    if not value:
        return None
    return _LOOKUP.get(compact_token(value), normalize_unknown(value))


def normalize_unknown(value: str) -> str:
    return normalize_display(value)


def normalize_display(value: str) -> str:
    return " ".join(value.strip().split())
