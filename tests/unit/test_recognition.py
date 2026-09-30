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
    # The third row has one clearly dominant option; a row of *identical* marks
    # has zero variance and is covered separately below.
    marks = np.array(
        [[100, 0, 0], [0, 100, 0], [50, 10, 0]],
        dtype=np.float64,
    )

    with subtests.test("probabilities are marks over area"):
        odds, _ = detect_selected_answer(marks, area=100, threshold=0.4)
        assert odds.shape == (3, 3)
        assert np.allclose(
            odds, [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.5, 0.1, 0.0]]
        )

    with subtests.test("clearly filled options are selected"):
        _, selected = detect_selected_answer(marks, area=100, threshold=0.4)
        assert selected.dtype == bool
        assert selected.tolist() == [
            [True, False, False],
            [False, True, False],
            [True, False, False],
        ]

    with subtests.test("two strong marks are both selected"):
        # Both marks clear the row mean and the threshold, so neither is dropped.
        double = np.array([[160.0, 4.0, 0.0, 155.0]])
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


def test_detect_selected_answer_uniform_rows(subtests):
    """On a uniform row the threshold decides blank vs marked.

    ``detect_selected_answer`` ANDs two conditions::

        (odds > 1.96 * std(odds)) & (odds >= threshold)

    When every option has the same value the standard deviation is 0, so the
    first condition degenerates to ``odds > 0`` and stops discriminating. The
    threshold is then what tells an all-blank row (low odds) apart from an
    all-marked row (high odds).
    """

    with subtests.test("the variance term is inert on a uniform row"):
        uniform = np.array([[50.0, 50.0, 50.0, 50.0]])
        odds, _ = detect_selected_answer(uniform, area=100, threshold=0.4)
        assert np.allclose(np.std(odds, axis=1), 0.0)

    with subtests.test("all blank stays unselected"):
        blank = np.array([[5.0, 5.0, 5.0, 5.0]])  # odds 0.05
        _, selected = detect_selected_answer(blank, area=100, threshold=0.4)
        assert not selected.any()

    with subtests.test("all marked is selected"):
        marked = np.array([[90.0, 90.0, 90.0, 90.0]])  # odds 0.90
        _, selected = detect_selected_answer(marked, area=100, threshold=0.4)
        assert selected.tolist() == [[True, True, True, True]]

    with subtests.test("lowering the threshold flips an all-blank row"):
        blank = np.array([[5.0, 5.0, 5.0, 5.0]])  # odds 0.05
        _, selected = detect_selected_answer(blank, area=100, threshold=0.01)
        assert selected.tolist() == [[True, True, True, True]]

    with subtests.test("the threshold comparison is inclusive"):
        boundary = np.array([[40.0, 40.0, 40.0, 40.0]])  # odds exactly 0.4
        _, selected = detect_selected_answer(boundary, area=100, threshold=0.4)
        assert selected.tolist() == [[True, True, True, True]]

    with subtests.test("just below the threshold is rejected"):
        below = np.array([[39.9, 39.9, 39.9, 39.9]])  # odds 0.399
        _, selected = detect_selected_answer(below, area=100, threshold=0.4)
        assert not selected.any()
