from __future__ import annotations

from dataclasses import dataclass

from hhpi.domain.models import Availability, OfferCandidate, PriceBasis
from hhpi.normalization.color import normalize_color
from hhpi.normalization.text import compact_token


@dataclass(frozen=True)
class BestPriceQuery:
    model: str
    storage_gb: int | None = None
    ram_gb: int | None = None
    network: str | None = None
    color: str | None = None
    price_basis: PriceBasis | None = None


@dataclass(frozen=True)
class RankedOffer:
    offer: OfferCandidate
    comparison_toman: int
    rank: int


def _model_matches(query: str, offer: OfferCandidate) -> bool:
    q = compact_token(query)
    candidates = [offer.model_canonical, offer.model_raw]
    return any(c and q in compact_token(c) for c in candidates)


def rank_offers(offers: list[OfferCandidate], query: BestPriceQuery) -> list[RankedOffer]:
    wanted_color = normalize_color(query.color) if query.color else None
    matched: list[tuple[int, OfferCandidate]] = []

    for offer in offers:
        if offer.needs_review:
            continue
        if offer.price.availability != Availability.AVAILABLE:
            continue
        if not _model_matches(query.model, offer):
            continue
        if query.storage_gb is not None and offer.storage_gb != query.storage_gb:
            continue
        if query.ram_gb is not None and offer.ram_gb != query.ram_gb:
            continue
        if query.network is not None and offer.network != query.network:
            continue
        if wanted_color is not None and normalize_color(offer.color_canonical or offer.color_raw) != wanted_color:
            continue
        if query.price_basis is not None and offer.price.basis != query.price_basis:
            continue

        comparison = offer.price.comparison_toman
        if comparison is None:
            continue
        matched.append((comparison, offer))

    matched.sort(key=lambda item: (item[0], item[1].supplier_id))
    return [RankedOffer(offer=o, comparison_toman=p, rank=i + 1) for i, (p, o) in enumerate(matched)]
