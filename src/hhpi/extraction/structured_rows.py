from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from hhpi.domain.models import PriceBasis, PriceValue
from hhpi.layout.segmentation import TableRow
from hhpi.normalization.price import parse_price
from hhpi.normalization.text import normalize_text
from hhpi.normalization.variant import MemoryVariant, parse_memory_variant
from .preprocess import PreprocessOptions
from .tesseract_engine import TesseractEngine


@dataclass(frozen=True)
class StructuredRowCandidate:
    row_index: int
    raw_model_text: str
    ram_gb: int | None
    storage_gb: int | None
    network: str | None
    color_text: str | None
    cash: PriceValue | None
    credit: PriceValue | None
    evidence: dict[str, str]


def _repair_digit_context(text: str) -> str:
    """Conservative OCR repair only inside digit-like tokens.

    Supplier fonts frequently make 5 look like S and 0 look like O. We repair only when the letter is
    adjacent to a digit or slash, never in free text/model names.
    """
    text = normalize_text(text)
    text = re.sub(r"(?<=\d)[sS](?=\d|[/\\-])", "5", text)
    text = re.sub(r"(?<=[/\\-])[sS](?=\d)", "5", text)
    text = re.sub(r"(?<=\D)[sS](?=\d{2,4}[/\\-]\d{1,2})", "5", text)
    text = re.sub(r"(?<=\d)[oO](?=\d)", "0", text)
    return text


def _network(text: str) -> str | None:
    compact = re.sub(r"\s+", "", normalize_text(text)).upper()
    match = re.search(r"([45])G", compact)
    return f"{match.group(1)}G" if match else None


def _strip_network_suffix(text: str) -> str:
    # OCR often glues `4G` directly to memory: `256/84G`. Remove only a terminal network token.
    return re.sub(r"([45])G(?=$|[^A-Z0-9])", "", normalize_text(text), flags=re.IGNORECASE)


def _parse_price_cell(raw: str, *, basis: PriceBasis, scale_toman: int) -> PriceValue | None:
    text = normalize_text(raw).strip()
    if not text:
        return None
    digits = [int(x) for x in re.findall(r"\d+", text.replace(",", ""))]
    # A lone OCR artifact such as `1` must never become 1,000 toman in a wholesale mobile list.
    if digits and max(digits) < 1000 and not any(k in text.lower() for k in ("call", "تماس", "soon", "***")):
        return None
    return parse_price(text, scale_toman=scale_toman, basis=basis)


class TesseractStructuredRowReader:
    """Read a known table schema row using separate OCR policies per cell type.

    Price cells use a digit-only whitelist and aggressive upscale. This is intentionally different from
    model/color OCR: critical numeric fields should not share the same recognition policy as prose.
    """

    def __init__(self) -> None:
        self.text_engine = TesseractEngine(
            languages="eng",
            psm=13,
            preprocess=PreprocessOptions(scale=8.0, clahe=False),
        )
        self.price_engine = TesseractEngine(
            languages="eng",
            psm=7,
            preprocess=PreprocessOptions(scale=10.0, clahe=False),
            extra_config="-c tessedit_char_whitelist=0123456789,-.*",
        )

    def read(
        self,
        image_path: str | Path,
        row: TableRow,
        *,
        roles: tuple[str, ...],
        scale_toman: int = 1000,
    ) -> StructuredRowCandidate:
        if len(row.cells) < len(roles):
            raise ValueError(f"row has {len(row.cells)} cells but schema needs {len(roles)}")

        values: dict[str, str] = {}
        for cell, role in zip(row.cells, roles):
            engine = self.price_engine if role in {"cash", "credit", "price"} else self.text_engine
            page = engine.extract(image_path, region=cell.bbox)
            values[role] = (page.raw_text or "").strip()

        model_text = values.get("model", "")
        repaired_model = _repair_digit_context(model_text)
        network = _network(repaired_model)
        memory = parse_memory_variant(_strip_network_suffix(repaired_model))

        cash = _parse_price_cell(values.get("cash", ""), basis=PriceBasis.CASH, scale_toman=scale_toman)
        credit = _parse_price_cell(values.get("credit", ""), basis=PriceBasis.CREDIT, scale_toman=scale_toman)
        if values.get("price") and cash is None:
            cash = _parse_price_cell(values["price"], basis=PriceBasis.SINGLE, scale_toman=scale_toman)

        return StructuredRowCandidate(
            row_index=row.index,
            raw_model_text=model_text,
            ram_gb=memory.ram_gb,
            storage_gb=memory.storage_gb,
            network=network,
            color_text=values.get("color") or None,
            cash=cash,
            credit=credit,
            evidence=values,
        )
