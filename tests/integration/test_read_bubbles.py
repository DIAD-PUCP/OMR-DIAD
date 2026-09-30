"""Integration test for bubble reading + answer extraction.

A synthetic page is drawn from the geometry of ``config.json`` with one known
option filled per item, then ``read_bubbles`` and ``process_mcq_marks`` are
run together. This isolates the recognition pipeline from PDF rendering.
"""

import cv2
import numpy as np

from omr_diad.processing import process_mcq_marks, read_bubbles


def draw_synthetic_page(config) -> tuple[np.ndarray, dict[int, str]]:
    height, width = config.page_size[1], config.page_size[0]
    image = np.full((height, width, 3), 255, dtype=np.uint8)
    expected: dict[int, str] = {}

    segment = config.segments[0]
    base = np.array(segment.position)
    for block in segment.item_blocks:
        for row in range(block.nrows):
            option = row % block.nopts
            item_size = np.array(block.item_size)
            center = (
                base
                + np.array(block.position)
                + np.array([option, row]) * item_size
                + item_size // 2
            )
            radius = block.bubble_size[0] // 2
            cv2.circle(
                image,
                (int(center[0]), int(center[1])),
                radius,
                (0, 0, 0),
                -1,
            )
            expected[block.labels[0] + row] = block.bubble_labels[option]
    return image, expected


def test_read_bubbles_matches_drawn_marks(config):
    image, expected = draw_synthetic_page(config)

    marks = read_bubbles(config, image)
    answers, _ = process_mcq_marks(config, marks)

    flat = [answer.strip() for block in answers for answer in block]
    assert len(flat) == 76
    assert flat == [expected[i] for i in range(1, 77)]


def test_filled_option_has_the_highest_mark(config):
    image, _ = draw_synthetic_page(config)

    marks = read_bubbles(config, image)

    first_block = marks[0]
    assert first_block.shape == (30, 4)
    # Row 0 was drawn with option 0 filled.
    assert int(np.argmax(first_block[0])) == 0
    # Rows 1..3 cycle through options 1..3.
    assert [int(np.argmax(first_block[r])) for r in range(4)] == [0, 1, 2, 3]
