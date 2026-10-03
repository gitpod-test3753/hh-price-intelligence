from pathlib import Path

import cv2
import numpy as np

from hhpi.classification.price_list import StructuralPriceListClassifier


def test_structural_classifier_separates_grid_from_blank(tmp_path: Path):
    grid = np.full((600, 600, 3), 255, dtype=np.uint8)
    for y in range(20, 580, 25):
        cv2.line(grid, (10, y), (590, y), (0, 0, 0), 1)
    for x in range(10, 591, 100):
        cv2.line(grid, (x, 20), (x, 575), (0, 0, 0), 1)
    grid_path = tmp_path / "grid.png"
    cv2.imwrite(str(grid_path), grid)

    blank = np.full((600, 600, 3), 255, dtype=np.uint8)
    blank_path = tmp_path / "blank.png"
    cv2.imwrite(str(blank_path), blank)

    classifier = StructuralPriceListClassifier()
    assert classifier.classify(grid_path).label == "price_list"
    assert classifier.classify(blank_path).label == "not_price_list"
