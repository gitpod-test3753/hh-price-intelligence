from datetime import datetime, timezone

from hhpi.domain.models import OfferCandidate
from hhpi.normalization.price import parse_price
from hhpi.query.best_price import BestPriceQuery
from hhpi.storage.db import Base, make_engine, make_session_factory
from hhpi.storage.repository import OfferRepository


def make_offer(supplier: str, price: str) -> OfferCandidate:
    return OfferCandidate(
        supplier_id=supplier,
        observed_at=datetime.now(timezone.utc),
        brand="Xiaomi",
        model_raw="Note 15 8/256 4G",
        model_canonical="Redmi Note 15",
        ram_gb=8,
        storage_gb=256,
        network="4G",
        color_raw="Black",
        color_canonical="black",
        price=parse_price(price),
        confidence_total=1.0,
    )


def test_append_only_and_active_query():
    engine = make_engine()
    Base.metadata.create_all(engine)
    Session = make_session_factory(engine)
    with Session() as session:
        repo = OfferRepository(session)
        old = repo.append(make_offer("supplier-a", "81000"))
        repo.append(make_offer("supplier-b", "80500"))
        session.commit()

        ranked = repo.best_price(BestPriceQuery(model="Note 15", storage_gb=256, color="black"))
        assert ranked[0].offer.supplier_id == "supplier-b"

        repo.supersede(old.id)
        session.commit()
        active = repo.list_active()
        assert {o.supplier_id for o in active} == {"supplier-b"}
