from __future__ import annotations

import cv2
import numpy as np

from hhpi.layout.models import BBox
from hhpi.layout.segmentation import SegmentConfig, segment_table


def test_segment_table_recovers_simple_grid(tmp_path):
    image = np.full((220, 320, 3), 255, dtype=np.uint8)
    for y in (20, 60, 100, 140, 180, 200):
        cv2.line(image, (20, y), (300, y), (0, 0, 0), 2)
    for x in (20, 160, 240, 300):
        cv2.line(image, (x, 20), (x, 200), (0, 0, 0), 2)
    path = tmp_path / "grid.png"
    cv2.imwrite(str(path), image)

    seg = segment_table(path, region=BBox(18, 18, 302, 202))
    assert len(seg.rows) == 5
    assert all(len(row.cells) == 3 for row in seg.rows)
    assert seg.rows[0].bbox.y1 < seg.rows[-1].bbox.y1


def test_segment_table_returns_source_space_boxes(tmp_path):
    image = np.full((180, 400, 3), 255, dtype=np.uint8)
    for y in (50, 80, 110, 140):
        cv2.line(image, (100, y), (300, y), (0, 0, 0), 2)
    for x in (100, 200, 300):
        cv2.line(image, (x, 50), (x, 140), (0, 0, 0), 2)
    path = tmp_path / "offset.png"
    cv2.imwrite(str(path), image)

    seg = segment_table(path, region=BBox(95, 45, 305, 145))
    assert seg.region.x1 == 95
    assert min(seg.vertical_separators) >= 95
    assert min(seg.horizontal_separators) >= 45
    assert all(cell.bbox.x1 >= 95 for row in seg.rows for cell in row.cells)


def test_refine_region_snaps_nearby_vertical_rules(tmp_path):
    from hhpi.layout.segmentation import refine_region_to_grid

    image = np.full((220, 360, 3), 255, dtype=np.uint8)
    # Strong full-height panel boundaries.
    cv2.line(image, (80, 0), (80, 219), (0, 0, 0), 3)
    cv2.line(image, (280, 0), (280, 219), (0, 0, 0), 3)
    # Enough horizontal rules to make this look table-like.
    for y in range(20, 210, 25):
        cv2.line(image, (80, y), (280, y), (0, 0, 0), 2)
    path = tmp_path / "snap.png"
    cv2.imwrite(str(path), image)

    refined = refine_region_to_grid(path, BBox(65, 10, 295, 210))
    assert abs(refined.x1 - 80) <= 2
    assert abs(refined.x2 - 280) <= 2
    assert refined.y1 == 10 and refined.y2 == 210
