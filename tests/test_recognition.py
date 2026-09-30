"""Unit tests for the numeric helpers in ``omr_diad.recognition``."""

import numpy as np
import pytest

from omr_diad.recognition import calculate_values, detect_selected_answer


def test_calculate_values(subtests):
    mask = np.array([[255, 0], [0, 255]], dtype=np.uint8)

    with subtests.test("masked overlap"):
        # Only the pixels where mask, aoi_bw and (255 - aoi_gray) overlap count.
        aoi_bw = np.array([[255, 255], [0, 0]], dtype=np.uint8)
        aoi_gray = np.array([[0, 255], [0, 0]], dtype=np.uint8)
        assert calculate_values(aoi_bw, aoi_gray, mask) == pytest.approx(1.0)

    with subtests.test("no marks"):
        zeros = np.zeros((2, 2), dtype=np.uint8)
        assert calculate_values(zeros, zeros, mask) == 0.0

    with subtests.test("empty mask"):
        filled = np.full((2, 2), 255, dtype=np.uint8)
        empty = np.zeros((2, 2), dtype=np.uint8)
        assert calculate_values(filled, empty, empty) == 0.0


def test_detect_selected_answer(subtests):
    marks = np.array(
        [[100, 0, 0], [0, 100, 0], [50, 50, 50]],
        dtype=np.float64,
    )

    with subtests.test("probabilities are marks over area"):
        odds, _ = detect_selected_answer(marks, area=100, threshold=0.4)
        assert odds.shape == (3, 3)
        assert np.allclose(
            odds, [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.5, 0.5, 0.5]]
        )

    with subtests.test("clearly filled options are selected"):
        _, selected = detect_selected_answer(marks, area=100, threshold=0.4)
        assert selected.dtype == bool
        assert selected.tolist() == [
            [True, False, False],
            [False, True, False],
            [False, False, False],
        ]

    with subtests.test("two strong marks are both selected"):
        # Both marks clear the row mean and the threshold, so neither is dropped.
        double = np.array([[160.0, 4.0, 0.0, 146.0]])
        _, selected = detect_selected_answer(double, area=100, threshold=0.4)
        assert selected.tolist() == [[True, False, False, True]]

    with subtests.test("threshold rejects a faint mark the mean test would keep"):
        faint = np.array([[35.0, 10.0, 5.0, 0.0]])
        _, selected = detect_selected_answer(faint, area=100, threshold=0.4)
        assert not selected.any()
        _, selected = detect_selected_answer(faint, area=100, threshold=0.2)
        assert selected.tolist() == [[True, False, False, False]]

    with subtests.test("output shape follows the input marks"):
        big = np.zeros((5, 4), dtype=np.float64)
        big[2, 3] = 100
        odds, selected = detect_selected_answer(big, area=100, threshold=0.4)
        assert odds.shape == (5, 4)
        assert selected.shape == (5, 4)
