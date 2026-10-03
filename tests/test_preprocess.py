import cv2
import numpy as np

from hhpi.extraction.preprocess import PreprocessOptions, preprocess_array


def test_preprocess_scales_and_grays():
    img = np.full((20, 30, 3), 255, dtype=np.uint8)
    cv2.putText(img, "15", (2, 16), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
    out = preprocess_array(img, PreprocessOptions(scale=2, clahe=True))
    assert out.shape == (40, 60)
