from datetime import datetime, timezone

from hhpi.domain.models import OfferCandidate
from hhpi.normalization.price import parse_price
from hhpi.query.best_price import BestPriceQuery, rank_offers


def make_offer(supplier: str, price_raw: str, color: str = "black") -> OfferCandidate:
    return OfferCandidate(
        supplier_id=supplier,
        observed_at=datetime.now(timezone.utc),
        brand="Xiaomi",
        model_raw="Note 15 8/256 4G",
        model_canonical="Redmi Note 15",
        ram_gb=8,
        storage_gb=256,
        network="4G",
        color_raw=color,
        color_canonical=color,
        price=parse_price(price_raw),
        confidence_total=1.0,
    )


def test_best_price_variant_aware_and_range_sorting():
    offers = [
        make_offer("a", "80500"),
        make_offer("b", "80000-80500"),
        make_offer("c", "81000"),
        make_offer("wrong-color", "79000", color="blue"),
    ]
    results = rank_offers(
        offers,
        BestPriceQuery(model="Note 15", storage_gb=256, ram_gb=8, network="4G", color="مشکی"),
    )
    assert [r.offer.supplier_id for r in results] == ["b", "a", "c"]
