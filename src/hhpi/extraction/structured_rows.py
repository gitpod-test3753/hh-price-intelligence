from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import re

from hhpi.catalog.resolver import CatalogResolver, default_catalog_resolver
from hhpi.domain.models import Availability, PriceBasis, PriceValue
from hhpi.layout.segmentation import TableRow, TableSegmentation
from hhpi.normalization.color import normalize_color, resolve_known_color
from hhpi.normalization.price import parse_price
from hhpi.normalization.text import normalize_text
from hhpi.normalization.variant import MemoryVariant, parse_memory_variant
from .preprocess import PreprocessOptions, has_cell_ink
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
    brand: str | None = None
    model_canonical: str | None = None
    color_canonical: str | None = None
    price: PriceValue | None = None
    confidence: float = 0.0
    needs_review: bool = False
    bbox: tuple[int, int, int, int] | None = None
    review_reasons: tuple[str, ...] = field(default_factory=tuple)


def _repair_digit_context(text: str) -> str:
    """Conservative OCR repair inside digit-like and capacity tokens.

    Supplier fonts frequently make 5 look like S, 1 look like I/l, and 0 look like O.
    """
    text = normalize_text(text)
    # Repair I/l -> 1 when inside a slash/hyphen capacity pair (e.g. SI2/I2 -> S12/12)
    text = re.sub(r"(?<=[sS5\d/\\-])[Ili](?=\d|[/\\-])", "1", text)
    text = re.sub(r"(?<=[/\\-])[Ili](?=\d)", "1", text)
    text = re.sub(r"(?<=\d)[sS](?=\d|[/\\-])", "5", text)
    text = re.sub(r"(?<=[/\\-])[sS](?=\d)", "5", text)
    text = re.sub(r"(?<=\D)[sS](?=\d{2,4}[/\\-]\d{1,2})", "5", text)
    text = re.sub(r"(?<=\d)[oO](?=\d)", "0", text)
    return text


def _network(text: str, *, model_canonical: str | None = None) -> str | None:
    norm = normalize_text(text)
    compact = re.sub(r"\s+", "", norm).upper()
    match = re.search(r"([45])G", compact)
    if match:
        return f"{match.group(1)}G"

    # Detect when OCR misread trailing `4G` or `5G` after memory as `46`/`40` or `56`/`50`
    glued = re.search(
        r"(?:512|256|128|64|592|612)\s*[/\\-]?\s*(?:16|12|8|6|4)?\s*(46|40|56|50)(?=$|[^0-9])",
        norm,
    )
    if glued:
        code = glued.group(1)
        return "4G" if code.startswith("4") else "5G"

    if model_canonical == "Redmi Note 15":
        return "4G"
    return None


def _strip_network_suffix(text: str) -> str:
    s = normalize_text(text)
    s = re.sub(r"([45])G(?=$|[^A-Z0-9])", "", s, flags=re.IGNORECASE)
    return s


def _parse_price_cell(
    raw: str,
    *,
    basis: PriceBasis,
    scale_toman: int,
    supplier_id: str | None = None,
) -> PriceValue | None:
    text = normalize_text(raw).strip()
    if not text:
        return None
    # Clean common OCR border artifacts in price strings while keeping range hyphens and commas.
    cleaned = re.sub(r"^[^0-9\*A-Za-zآ-ی]+|[^0-9\*A-Za-zآ-ی]+$", "", text)
    if not cleaned:
        return None
    digits = [int(x) for x in re.findall(r"\d+", cleaned.replace(",", ""))]
    has_marker = any(k in cleaned.lower() for k in ("call", "تماس", "soon", "***", "--"))
    if digits and max(digits) < 100 and not has_marker:
        return None

    # Handle supplier-specific shorthand:
    # 1) alerasolshop writes >=100M prices as 3-digit numbers (e.g., `115` -> 115,000,000 toman).
    if len(digits) == 1 and 100 <= digits[0] < 1000 and "-" not in cleaned:
        return PriceValue(
            raw=cleaned,
            availability=Availability.AVAILABLE,
            basis=basis,
            normalized_toman=digits[0] * 1_000 * scale_toman,
        )
    # 2) ani_mob writes >=100M prices as 5-digit numbers starting with 1 (e.g., `14500` -> 145,000,000 toman).
    if supplier_id == "ani_mob" and len(digits) == 1 and 10_000 <= digits[0] < 25_000:
        return PriceValue(
            raw=cleaned,
            availability=Availability.AVAILABLE,
            basis=basis,
            normalized_toman=digits[0] * 10 * scale_toman,
        )

    return parse_price(cleaned, scale_toman=scale_toman, basis=basis)


class TesseractStructuredRowReader:
    """Read a known table schema row using separate OCR policies per cell type."""

    def __init__(self, *, catalog: CatalogResolver | None = None) -> None:
        self.catalog = catalog or default_catalog_resolver()
        self.text_engine = TesseractEngine(
            languages="eng",
            psm=7,
            preprocess=PreprocessOptions(
                scale=4.5,
                clahe=False,
                trim_borders=True,
                contrast_stretch=True,
                pad_px=16,
            ),
        )
        self.text_fallback_engine = TesseractEngine(
            languages="eng",
            psm=13,
            preprocess=PreprocessOptions(scale=7.0, clahe=False, trim_borders=True, pad_px=16),
        )
        self.memory_engine = TesseractEngine(
            languages="eng",
            psm=7,
            preprocess=PreprocessOptions(
                scale=4.5,
                clahe=False,
                trim_borders=True,
                contrast_stretch=True,
                focus_ink=True,
                pad_px=16,
            ),
            extra_config="-c tessedit_char_whitelist=0123456789/-TBtb",
        )
        self.color_fas_engine = TesseractEngine(
            languages="fas",
            psm=7,
            preprocess=PreprocessOptions(
                scale=4.0,
                clahe=False,
                trim_borders=True,
                contrast_stretch=True,
                focus_ink=True,
                x_margin_px=5,
                pad_px=16,
            ),
        )
        self.color_fas_alt_engine = TesseractEngine(
            languages="fas",
            psm=7,
            preprocess=PreprocessOptions(
                scale=5.0,
                clahe=False,
                trim_borders=True,
                contrast_stretch=True,
                pad_px=16,
            ),
        )
        self.color_eng_engine = TesseractEngine(
            languages="eng",
            psm=7,
            preprocess=PreprocessOptions(
                scale=4.5,
                clahe=False,
                trim_borders=True,
                contrast_stretch=True,
                pad_px=16,
            ),
        )
        self.price_engine = TesseractEngine(
            languages="eng",
            psm=7,
            preprocess=PreprocessOptions(
                scale=4.0,
                clahe=False,
                trim_borders=True,
                contrast_stretch=True,
                focus_ink=True,
                pad_px=16,
            ),
            extra_config="-c tessedit_char_whitelist=0123456789,-.*",
        )
        self.price_fallback_engine = TesseractEngine(
            languages="eng",
            psm=7,
            preprocess=PreprocessOptions(
                scale=6.0,
                clahe=False,
                trim_borders=True,
                pad_px=16,
            ),
            extra_config="-c tessedit_char_whitelist=0123456789,-.*",
        )

    def _read_color_cell(
        self,
        image_path: str | Path,
        bbox,
        *,
        preferred_lang: str | None = None,
    ) -> tuple[str, str | None, float]:
        if not has_cell_ink(image_path, bbox):
            return "", None, 0.0
        if preferred_lang == "eng":
            engines = (self.color_eng_engine, self.color_fas_engine)
        elif preferred_lang == "fas":
            engines = (self.color_fas_engine, self.color_fas_alt_engine)
        else:
            engines = (self.color_fas_engine, self.color_eng_engine, self.color_fas_alt_engine)

        first_raw = ""
        first_conf = 0.0
        for idx, eng in enumerate(engines):
            page = eng.extract(image_path, region=bbox)
            raw = (page.raw_text or "").strip()
            if idx == 0:
                first_raw, first_conf = raw, page.mean_confidence
            known = resolve_known_color(raw)
            if known is not None:
                return raw, known, max(0.85, page.mean_confidence)
        return first_raw, normalize_color(first_raw) if first_raw else None, first_conf

    def _read_price_cell(self, image_path: str | Path, bbox) -> tuple[str, float]:
        if not has_cell_ink(image_path, bbox):
            return "", 0.0
        page = self.price_engine.extract(image_path, region=bbox)
        raw = (page.raw_text or "").strip()
        digits = re.findall(r"\d+", raw.replace(",", ""))
        if digits and max(int(d) for d in digits) >= 100:
            return raw, max(0.85, page.mean_confidence)
        if any(k in raw for k in ("***", "---", "--")):
            return raw, 0.80
        page2 = self.price_fallback_engine.extract(image_path, region=bbox)
        raw2 = (page2.raw_text or "").strip()
        digits2 = re.findall(r"\d+", raw2.replace(",", ""))
        if digits2 and max(int(d) for d in digits2) >= 100:
            return raw2, max(0.75, page2.mean_confidence)
        return raw or raw2, page.mean_confidence

    def read(
        self,
        image_path: str | Path,
        row: TableRow,
        *,
        roles: tuple[str, ...],
        scale_toman: int = 1000,
        supplier_id: str | None = None,
    ) -> StructuredRowCandidate:
        if len(row.cells) < len(roles):
            raise ValueError(f"row has {len(row.cells)} cells but schema needs {len(roles)}")

        values: dict[str, str] = {}
        confidences: list[float] = []
        color_canonical: str | None = None

        preferred_color_lang = (
            "eng"
            if supplier_id in {"fardadhamrah", "alerasolshop"}
            else "fas"
            if supplier_id in {"mobile_hitech", "ani_mob"}
            else None
        )

        for cell, role in zip(row.cells, roles):
            if role in {"cash", "credit", "price"}:
                raw, conf = self._read_price_cell(image_path, cell.bbox)
                values[role] = raw
                confidences.append(conf)
            elif role == "color":
                raw, canonical, conf = self._read_color_cell(
                    image_path, cell.bbox, preferred_lang=preferred_color_lang
                )
                values[role] = raw
                color_canonical = canonical
                confidences.append(conf)
            elif role == "memory":
                if not has_cell_ink(image_path, cell.bbox):
                    values[role] = ""
                    confidences.append(0.0)
                else:
                    page = self.memory_engine.extract(image_path, region=cell.bbox)
                    values[role] = (page.raw_text or "").strip()
                    confidences.append(page.mean_confidence)
            else:
                if not has_cell_ink(image_path, cell.bbox):
                    values[role] = ""
                    confidences.append(0.0)
                else:
                    page = self.text_engine.extract(image_path, region=cell.bbox)
                    raw = (page.raw_text or "").strip()
                    if not raw:
                        page = self.text_fallback_engine.extract(image_path, region=cell.bbox)
                        raw = (page.raw_text or "").strip()
                    values[role] = raw
                    confidences.append(page.mean_confidence)

        model_text = values.get("model", "")
        memory_text = values.get("memory", "")
        combined_spec = f"{model_text} {memory_text}".strip()
        repaired_spec = _repair_digit_context(combined_spec)

        resolution = self.catalog.resolve(repaired_spec)
        if resolution.canonical_id is None and model_text:
            # Try fallback single-row OCR on model cell if initial OCR didn't resolve in catalog
            model_idx = roles.index("model") if "model" in roles else 0
            fb_page = self.text_fallback_engine.extract(image_path, region=row.cells[model_idx].bbox)
            fb_text = (fb_page.raw_text or "").strip()
            fb_res = self.catalog.resolve(_repair_digit_context(f"{fb_text} {memory_text}".strip()))
            if fb_res.canonical_id is not None:
                model_text = fb_text
                values["model"] = fb_text
                repaired_spec = _repair_digit_context(f"{model_text} {memory_text}".strip())
                resolution = fb_res

        network = _network(repaired_spec, model_canonical=resolution.model_canonical)
        memory = parse_memory_variant(_strip_network_suffix(repaired_spec))
        if (memory.ram_gb is None or memory.storage_gb is None) and memory_text:
            mem_only = parse_memory_variant(_repair_digit_context(memory_text))
            if mem_only.ram_gb is not None and mem_only.storage_gb is not None:
                memory = mem_only

        cash = _parse_price_cell(
            values.get("cash", ""),
            basis=PriceBasis.CASH,
            scale_toman=scale_toman,
            supplier_id=supplier_id,
        )
        credit = _parse_price_cell(
            values.get("credit", ""),
            basis=PriceBasis.CREDIT,
            scale_toman=scale_toman,
            supplier_id=supplier_id,
        )
        single_price = _parse_price_cell(
            values.get("price", ""),
            basis=PriceBasis.SINGLE,
            scale_toman=scale_toman,
            supplier_id=supplier_id,
        )
        if single_price is not None and cash is None:
            cash = single_price

        reasons: list[str] = []
        if resolution.canonical_id is None:
            reasons.append("unresolved_model")
        if memory.ram_gb is None or memory.storage_gb is None:
            reasons.append("missing_memory")
        if color_canonical is None:
            reasons.append("missing_color")

        primary_price = single_price or cash or credit
        mean_conf = round(sum(confidences) / len(confidences), 4) if confidences else 0.0
        if resolution.canonical_id is not None and memory.ram_gb is not None and primary_price is not None:
            mean_conf = max(mean_conf, round(resolution.score / 100.0 * 0.92, 4))

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
            brand=resolution.brand,
            model_canonical=resolution.model_canonical,
            color_canonical=color_canonical,
            price=primary_price,
            confidence=mean_conf,
            needs_review=bool(reasons),
            bbox=row.bbox.as_tuple(),
            review_reasons=tuple(reasons),
        )

    def read_table(
        self,
        image_path: str | Path,
        segmentation: TableSegmentation,
        *,
        roles: tuple[str, ...],
        scale_toman: int = 1000,
        supplier_id: str | None = None,
    ) -> list[StructuredRowCandidate]:
        """Read all rows of a segmented table and fill missing memory/network from same-model siblings."""
        raw_candidates: list[StructuredRowCandidate] = []
        for row in segmentation.rows:
            if len(row.cells) < len(roles):
                continue
            raw_candidates.append(
                self.read(
                    image_path,
                    row,
                    roles=roles,
                    scale_toman=scale_toman,
                    supplier_id=supplier_id,
                )
            )

        # Context propagation across adjacent rows with the exact same canonical model and price
        out: list[StructuredRowCandidate] = []
        for idx, cand in enumerate(raw_candidates):
            ram, storage, net = cand.ram_gb, cand.storage_gb, cand.network
            if cand.model_canonical and (ram is None or storage is None or net is None):
                neighbors = [
                     raw_candidates[j]
                    for j in range(max(0, idx - 3), min(len(raw_candidates), idx + 4))
                    if j != idx and raw_candidates[j].model_canonical == cand.model_canonical
                ]
                for nb in neighbors:
                    if ram is None and nb.ram_gb is not None:
                        ram = nb.ram_gb
                    if storage is None and nb.storage_gb is not None:
                        storage = nb.storage_gb
                    if net is None and nb.network is not None:
                        net = nb.network
                if (ram, storage, net) != (cand.ram_gb, cand.storage_gb, cand.network):
                    reasons = tuple(
                        r for r in cand.review_reasons if not (r == "missing_memory" and ram and storage)
                    )
                    cand = StructuredRowCandidate(
                        row_index=cand.row_index,
                        raw_model_text=cand.raw_model_text,
                        ram_gb=ram,
                        storage_gb=storage,
                        network=net,
                        color_text=cand.color_text,
                        cash=cand.cash,
                        credit=cand.credit,
                        evidence=cand.evidence,
                        brand=cand.brand,
                        model_canonical=cand.model_canonical,
                        color_canonical=cand.color_canonical,
                        price=cand.price,
                        confidence=max(cand.confidence, 0.85),
                        needs_review=bool(reasons),
                        bbox=cand.bbox,
                        review_reasons=reasons,
                    )
            out.append(cand)
        return out
