from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field


class Availability(StrEnum):
    AVAILABLE = "available"
    CALL = "call_for_price"
    SOON = "coming_soon"
    UNPRICED = "unpriced"
    UNKNOWN = "unknown"


class Condition(StrEnum):
    NEW = "new"
    USED = "used"
    UNKNOWN = "unknown"


class PriceBasis(StrEnum):
    SINGLE = "single"
    RANGE = "range"
    CASH = "cash"
    CREDIT = "credit"
    UNKNOWN = "unknown"


class FieldEvidence(BaseModel):
    raw_text: str | None = None
    confidence: float = Field(default=0.0, ge=0, le=1)
    engine: str | None = None
    bbox: tuple[int, int, int, int] | None = None


class PriceValue(BaseModel):
    raw: str
    availability: Availability
    basis: PriceBasis = PriceBasis.UNKNOWN
    normalized_toman: int | None = None
    min_toman: int | None = None
    max_toman: int | None = None

    @property
    def comparison_toman(self) -> int | None:
        """Value used for sorting only; the original quote/range must still be displayed."""
        if self.normalized_toman is not None:
            return self.normalized_toman
        return self.min_toman


class OfferCandidate(BaseModel):
    supplier_id: str
    source_message_id: str | None = None
    source_image_id: str | None = None
    observed_at: datetime

    brand: str | None = None
    model_raw: str
    model_canonical: str | None = None
    ram_gb: int | None = None
    storage_gb: int | None = None
    network: Literal["4G", "5G"] | None = None
    color_raw: str | None = None
    color_canonical: str | None = None
    region: str | None = None
    warranty: str | None = None
    registration: str | None = None
    condition: Condition = Condition.NEW
    price: PriceValue

    evidence: dict[str, FieldEvidence] = Field(default_factory=dict)
    confidence_total: float = Field(default=0.0, ge=0, le=1)
    needs_review: bool = False
