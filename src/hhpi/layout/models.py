from __future__ import annotations

from dataclasses import dataclass, asdict


@dataclass(frozen=True)
class BBox:
    x1: int
    y1: int
    x2: int
    y2: int

    @property
    def width(self) -> int:
        return max(0, self.x2 - self.x1)

    @property
    def height(self) -> int:
        return max(0, self.y2 - self.y1)

    @property
    def area(self) -> int:
        return self.width * self.height

    def as_tuple(self) -> tuple[int, int, int, int]:
        return self.x1, self.y1, self.x2, self.y2


@dataclass(frozen=True)
class StructuralProfile:
    width: int
    height: int
    aspect_ratio: float
    ink_ratio: float
    horizontal_line_ratio: float
    vertical_line_ratio: float
    horizontal_lines: tuple[int, ...]
    vertical_lines: tuple[int, ...]
    table_likelihood: float

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class SupplierTemplateSchema:
    supplier_id: str
    region_name: str
    bbox_norm: tuple[float, float, float, float]
    roles: tuple[str, ...]
    column_splits: tuple[float, ...] = ()
    scale_toman: int = 1000
    snap_to_grid: bool = True

    def to_bbox(self, width: int, height: int) -> BBox:
        x1, y1, x2, y2 = self.bbox_norm
        return BBox(int(round(x1 * width)), int(round(y1 * height)), int(round(x2 * width)), int(round(y2 * height)))

