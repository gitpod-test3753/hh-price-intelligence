from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Query, Request

from hhpi.domain.models import PriceBasis
from hhpi.query.best_price import BestPriceQuery
from hhpi.storage.db import Base, make_engine, make_session_factory
from hhpi.storage.repository import OfferRepository


def _database_url() -> str:
    return os.getenv("DATABASE_URL", "sqlite+pysqlite:///./hhpi.db")


@asynccontextmanager
async def lifespan(app: FastAPI):
    engine = make_engine(_database_url())
    Base.metadata.create_all(engine)
    app.state.engine = engine
    app.state.Session = make_session_factory(engine)
    yield
    engine.dispose()


app = FastAPI(title="HH Price Intelligence", version="0.4.0", lifespan=lifespan)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "version": "0.4.0"}


@app.get("/v1/best-price")
def best_price(
    request: Request,
    model: str = Query(...),
    storage_gb: int | None = None,
    ram_gb: int | None = None,
    network: str | None = None,
    color: str | None = None,
    price_basis: PriceBasis | None = None,
) -> dict:
    query = BestPriceQuery(
        model=model,
        storage_gb=storage_gb,
        ram_gb=ram_gb,
        network=network,
        color=color,
        price_basis=price_basis,
    )
    with request.app.state.Session() as session:
        results = OfferRepository(session).best_price(query)

    return {
        "query": {
            "model": model,
            "storage_gb": storage_gb,
            "ram_gb": ram_gb,
            "network": network,
            "color": color,
            "price_basis": price_basis.value if price_basis else None,
        },
        "matches": [
            {
                "rank": r.rank,
                "supplier_id": r.offer.supplier_id,
                "model": r.offer.model_canonical or r.offer.model_raw,
                "ram_gb": r.offer.ram_gb,
                "storage_gb": r.offer.storage_gb,
                "network": r.offer.network,
                "color": r.offer.color_canonical or r.offer.color_raw,
                "price": r.offer.price.model_dump(mode="json"),
                "comparison_toman": r.comparison_toman,
                "source_image_id": r.offer.source_image_id,
                "source_message_id": r.offer.source_message_id,
            }
            for r in results
        ],
    }
