from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from hhpi.domain.models import OfferCandidate, PriceValue
from hhpi.storage.db import Base, make_engine, make_session_factory
from hhpi.storage.repository import OfferRepository


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    db_path = root / "benchmarks" / "demo.sqlite"
    if db_path.exists():
        db_path.unlink()
    engine = make_engine(f"sqlite+pysqlite:///{db_path}")
    Base.metadata.create_all(engine)
    Session = make_session_factory(engine)

    seed = root / "benchmarks" / "ground_truth" / "seed_note15.jsonl"
    with Session() as session:
        repo = OfferRepository(session)
        for line in seed.read_text(encoding="utf-8").splitlines():
            row = json.loads(line)
            repo.append(
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
        session.commit()
    print(db_path)


if __name__ == "__main__":
    main()
