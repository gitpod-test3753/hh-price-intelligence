from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from hhpi.domain.models import OfferCandidate, PriceValue
from hhpi.query.best_price import BestPriceQuery, rank_offers


def load_seed(path: Path) -> list[OfferCandidate]:
    offers = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        offers.append(
            OfferCandidate(
                supplier_id=row["supplier_id"],
                source_image_id=row["image_id"],
                observed_at=datetime(2026, 9, 29, tzinfo=timezone.utc),
                brand=row["brand"],
                model_raw=row["model_raw"],
                model_canonical=row["model_canonical"],
                ram_gb=row["ram_gb"],
                storage_gb=row["storage_gb"],
                network=row["network"],
                color_raw=row["color_raw"],
                color_canonical=row["color_canonical"],
                price=PriceValue(raw=row["price_raw"], **row["price"]),
                confidence_total=1.0,
            )
        )
    return offers


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    offers = load_seed(root / "benchmarks" / "ground_truth" / "seed_note15.jsonl")
    query = BestPriceQuery(model="Note 15", storage_gb=256, ram_gb=8, network="4G", color="مشکی")
    for result in rank_offers(offers, query):
        p = result.offer.price
        print(
            result.rank,
            result.offer.supplier_id,
            p.raw,
            p.basis.value,
            result.comparison_toman,
            result.offer.source_image_id,
        )
