from __future__ import annotations

from dataclasses import dataclass

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


class CatalogResolver:
    def __init__(self, items: list[CatalogItem]) -> None:
        self.items = items
        self._aliases: dict[str, CatalogItem] = {}
        self._display_by_key: dict[str, str] = {}
        for item in items:
            values = (item.model, *item.aliases)
            for value in values:
                key = compact_token(value)
                self._aliases[key] = item
                self._display_by_key[key] = normalize_text(value)

    def resolve(self, raw: str, *, threshold: float = 88.0) -> Resolution:
        key = compact_token(raw)
        if key in self._aliases:
            return Resolution(self._aliases[key].canonical_id, 100.0, self._display_by_key[key], "exact_alias")

        match = process.extractOne(key, self._aliases.keys(), scorer=fuzz.WRatio, score_cutoff=threshold)
        if not match:
            return Resolution(None, 0.0, None, "unresolved")
        alias_key, score, _ = match
        return Resolution(
            self._aliases[alias_key].canonical_id,
            round(float(score), 2),
            self._display_by_key[alias_key],
            "fuzzy_alias",
        )
