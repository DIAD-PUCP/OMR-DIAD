"""End-to-end tests that run the full pipeline over the sample PDFs.

The expected rows live in ``tests/test2.csv`` and ``tests/test3.csv`` and are
regression baselines for the current detection parameters.
"""

import csv
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np

from omr_diad.form import Form
from omr_diad.main import proc_img, read_images
from tests.conftest import SAMPLES

TESTS = Path(__file__).resolve().parent
INPUTS = TESTS.parent / "inputs"


def read_golden(name: str) -> list[list[str]]:
    with (TESTS / name).open() as f:
        return list(csv.reader(f))


def test_form_diad(subtests):
    config = Form.model_validate_json((SAMPLES / "config.json").read_text())
    golden = read_golden("test3.csv")
    pages = read_images(INPUTS / "test3.pdf", False)
    assert len(pages) == len(golden)

    with (
        TemporaryDirectory() as out,
        TemporaryDirectory() as debug,
        TemporaryDirectory() as error,
    ):
        for i, (page, expected) in enumerate(zip(pages, golden)):
            data = (
                i,
                Path("test3.pdf"),
                config,
                np.array(page),
                out,
                debug,
                error,
                None,
                "",
            )
            with subtests.test("DIAD test forms", name=f"test3.pdf ({i + 1})"):
                assert proc_img(data) == expected


def test_formreturn_diad(subtests):
    config = Form.model_validate_json(
        (SAMPLES / "config_formreturn_diad.json").read_text()
    )
    golden = read_golden("test2.csv")
    pages = read_images(INPUTS / "calibracion.pdf", True)
    assert len(pages) == len(golden)

    with (
        TemporaryDirectory() as out,
        TemporaryDirectory() as debug,
        TemporaryDirectory() as error,
    ):
        for i, (page, expected) in enumerate(zip(pages, golden)):
            data = (
                i,
                Path("calibracion.pdf"),
                config,
                np.array(page),
                out,
                debug,
                error,
                None,
                "",
            )
            with subtests.test(
                "DIAD test formreturn forms", name=f"calibracion.pdf ({i + 1})"
            ):
                assert proc_img(data) == expected
