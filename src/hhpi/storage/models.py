from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


class SupplierRow(Base):
    __tablename__ = "suppliers"

    id: Mapped[str] = mapped_column(String(120), primary_key=True)
    display_name: Mapped[str | None] = mapped_column(String(240), nullable=True)
    channel_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)

    offers: Mapped[list["OfferVersionRow"]] = relationship(back_populates="supplier")


class OfferVersionRow(Base):
    __tablename__ = "offer_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    supplier_id: Mapped[str] = mapped_column(ForeignKey("suppliers.id"), index=True)
    source_message_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    source_image_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)

    brand: Mapped[str | None] = mapped_column(String(120), nullable=True)
    model_raw: Mapped[str] = mapped_column(Text)
    model_canonical: Mapped[str | None] = mapped_column(String(255), index=True, nullable=True)
    ram_gb: Mapped[int | None] = mapped_column(Integer, nullable=True)
    storage_gb: Mapped[int | None] = mapped_column(Integer, nullable=True)
    network: Mapped[str | None] = mapped_column(String(8), nullable=True)
    color_raw: Mapped[str | None] = mapped_column(String(120), nullable=True)
    color_canonical: Mapped[str | None] = mapped_column(String(120), index=True, nullable=True)
    condition: Mapped[str] = mapped_column(String(24), default="new")

    price_raw: Mapped[str] = mapped_column(String(120))
    price_availability: Mapped[str] = mapped_column(String(32), index=True)
    price_basis: Mapped[str] = mapped_column(String(24), index=True)
    price_normalized_toman: Mapped[int | None] = mapped_column(Integer, nullable=True)
    price_min_toman: Mapped[int | None] = mapped_column(Integer, nullable=True)
    price_max_toman: Mapped[int | None] = mapped_column(Integer, nullable=True)

    confidence_total_milli: Mapped[int] = mapped_column(Integer, default=0)
    needs_review: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    superseded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    supplier: Mapped[SupplierRow] = relationship(back_populates="offers")
