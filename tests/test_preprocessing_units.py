"""Unit tests for the image-analysis helpers in ``omr_diad.preprocessing``
that can be exercised without a real scan.
"""

import numpy as np
import pytest

from omr_diad.preprocessing import crop_black_edges, find_skew_timing_marks


def test_find_skew_timing_marks(subtests):
    with subtests.test("sloped timing marks"):
        # Rects are [x, y, width, height]; the first and last by x define the
        # line whose angle is returned.
        marks = np.array(
            [
                [10.0, 0.0, 5.0, 10.0],
                [100.0, 10.0, 5.0, 10.0],
                [55.0, 5.0, 5.0, 10.0],
            ]
        )
        angle, x, y = find_skew_timing_marks(marks)
        assert angle == pytest.approx(6.34, abs=0.01)
        assert x == 10.0
        assert y == 0.0

    with subtests.test("horizontal timing marks"):
        marks = np.array(
            [
                [10.0, 5.0, 5.0, 10.0],
                [100.0, 5.0, 5.0, 10.0],
                [55.0, 5.0, 5.0, 10.0],
            ]
        )
        angle, x, y = find_skew_timing_marks(marks)
        assert angle == pytest.approx(0.0)
        assert x == 10.0
        assert y == 5.0


def test_crop_black_edges(subtests):
    with subtests.test("crops to the bright content"):
        img = np.zeros((10, 10, 3), dtype=np.uint8)
        img[2:6, 3:8] = 255
        cropped = crop_black_edges(img)
        # numpy slices exclude the max index, so the bounding box is one pixel
        # smaller at the bottom/right edges.
        assert cropped.shape == (3, 4, 3)
        assert np.all(cropped == 255)

    with subtests.test("threshold keeps darker pixels"):
        img = np.zeros((5, 5, 3), dtype=np.uint8)
        img[1:4, 1:4] = 50
        cropped = crop_black_edges(img, threshold=40)
        assert cropped.shape == (2, 2, 3)  # 3x3 region -> 2x2 after max-exclusion

    with subtests.test("fully black image has no content"):
        # Documented limitation: an all-black image makes the bounding-box
        # reduction fail.
        with pytest.raises(ValueError):
            crop_black_edges(np.zeros((5, 5, 3), dtype=np.uint8))
