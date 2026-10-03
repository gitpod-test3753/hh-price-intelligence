from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from hhpi.domain.models import Condition, OfferCandidate, PriceBasis, PriceValue
from hhpi.query.best_price import BestPriceQuery, RankedOffer, rank_offers
from .models import OfferVersionRow, SupplierRow


class OfferRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def ensure_supplier(self, supplier_id: str, *, display_name: str | None = None, channel_ref: str | None = None) -> SupplierRow:
        row = self.session.get(SupplierRow, supplier_id)
        if row is None:
            row = SupplierRow(id=supplier_id, display_name=display_name, channel_ref=channel_ref)
            self.session.add(row)
            self.session.flush()
        return row

    def append(self, offer: OfferCandidate) -> OfferVersionRow:
        self.ensure_supplier(offer.supplier_id)
        row = OfferVersionRow(
            supplier_id=offer.supplier_id,
            source_message_id=offer.source_message_id,
            source_image_id=offer.source_image_id,
            observed_at=offer.observed_at,
            brand=offer.brand,
            model_raw=offer.model_raw,
            model_canonical=offer.model_canonical,
            ram_gb=offer.ram_gb,
            storage_gb=offer.storage_gb,
            network=offer.network,
            color_raw=offer.color_raw,
            color_canonical=offer.color_canonical,
            condition=offer.condition.value,
            price_raw=offer.price.raw,
            price_availability=offer.price.availability.value,
            price_basis=offer.price.basis.value,
            price_normalized_toman=offer.price.normalized_toman,
            price_min_toman=offer.price.min_toman,
            price_max_toman=offer.price.max_toman,
            confidence_total_milli=round(offer.confidence_total * 1000),
            needs_review=offer.needs_review,
            active=True,
        )
        self.session.add(row)
        self.session.flush()
        return row

    def supersede(self, row_id: int, *, at: datetime | None = None) -> None:
        row = self.session.get(OfferVersionRow, row_id)
        if row is None:
            raise KeyError(row_id)
        if not row.active:
            return
        row.active = False
        row.superseded_at = at or datetime.now(timezone.utc)
        self.session.flush()

    def list_active(self) -> list[OfferCandidate]:
        stmt: Select = select(OfferVersionRow).where(OfferVersionRow.active.is_(True))
        rows = list(self.session.scalars(stmt))
        return [self._to_domain(row) for row in rows]

    def best_price(self, query: BestPriceQuery) -> list[RankedOffer]:
        # Keep ranking semantics centralized in the domain/query layer for now.
        # SQL pushdown can be added once benchmark semantics are stable.
        return rank_offers(self.list_active(), query)

    @staticmethod
    def _to_domain(row: OfferVersionRow) -> OfferCandidate:
        return OfferCandidate(
            supplier_id=row.supplier_id,
            source_message_id=row.source_message_id,
            source_image_id=row.source_image_id,
            observed_at=row.observed_at,
            brand=row.brand,
            model_raw=row.model_raw,
            model_canonical=row.model_canonical,
            ram_gb=row.ram_gb,
            storage_gb=row.storage_gb,
            network=row.network,
            color_raw=row.color_raw,
            color_canonical=row.color_canonical,
            condition=Condition(row.condition),
            price=PriceValue(
                raw=row.price_raw,
                availability=row.price_availability,
                basis=PriceBasis(row.price_basis),
                normalized_toman=row.price_normalized_toman,
                min_toman=row.price_min_toman,
                max_toman=row.price_max_toman,
            ),
            confidence_total=row.confidence_total_milli / 1000,
            needs_review=row.needs_review,
        )
