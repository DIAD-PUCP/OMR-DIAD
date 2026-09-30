"""Integration tests for ``omr_diad.processing.process_form`` and the CLI's
``proc_img`` worker (including its error path).
"""

from pathlib import Path

import numpy as np
import pytest

from omr_diad.main import proc_img, read_images
from omr_diad.processing import process_form
from tests.comparison import compare_rows
from tests.conftest import EXPECTED, PDFS, read_rows


def test_process_form_writes_artifacts_and_returns_a_row(config, tmp_path):
    out = tmp_path / "out"
    debug = tmp_path / "debug"
    out.mkdir()
    debug.mkdir()

    page = read_images(PDFS / "test3.pdf", convert_image=False)[0]
    row = process_form(
        config,
        np.array(page),
        output_dir=str(out),
        debug_dir=str(debug),
        extra={
            "filename": Path("test3.pdf"),
            "page_num": 1,
            "data": None,
            "data_key": "",
        },
    )

    labels = config.get_header()[1:]
    golden = read_rows(EXPECTED / "test3.csv")
    pairs = [
        (
            str(row[0]),
            dict(zip(labels, row[1:])),
            dict(zip(labels, golden[0][1:])),
        )
    ]
    # Same tolerant comparison as the E2E suite (2 allowlisted partial marks).
    compare_rows(pairs, max_diffs=2).raise_for_status()
    form_id = str(row[0])
    assert (out / f"{form_id} (test3.pdf 1).png").exists()
    assert (debug / f"{form_id} (test3.pdf 1).png").exists()


def test_proc_img_missing_barcode_is_captured(barcode_config, tmp_path):
    out = tmp_path / "out"
    debug = tmp_path / "debug"
    error = tmp_path / "error"
    for directory in (out, debug, error):
        directory.mkdir()

    # A blank page has no segment barcodes, so preprocessing raises.
    blank = np.full((400, 400, 3), 255, dtype=np.uint8)
    data = (
        0,
        Path("blank.pdf"),
        barcode_config,
        blank,
        str(out),
        str(debug),
        str(error),
        None,
        "",
    )

    assert proc_img(data) is None
    # proc_img names the capture "({page})_{stem}.png".
    assert (error / "(1)_blank.png").exists()
    assert not any(out.iterdir())
