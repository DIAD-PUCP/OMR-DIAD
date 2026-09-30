"""Regenerate golden files used by the test suite.

Run manually after an intentional detection change::

    python -m tests.tools.update_goldens

It currently regenerates the single-page goldens for the DIAD test forms
(``tests/fixtures/pdfs/test.pdf`` and friends). The larger goldens
(``ars271c2.csv``, ``LUCET262_pot_formreturn.csv``, ...) are full process
exports and are kept as-is; use ``--diff`` to print how the current code
compares against them before deciding whether to refresh them.
"""

from __future__ import annotations

import argparse
import csv
import sys
import tempfile
from pathlib import Path

import numpy as np

from omr_diad.form import Form
from omr_diad.main import read_images
from omr_diad.processing import process_form

ROOT = Path(__file__).resolve().parents[2]
PDFS = ROOT / "tests" / "fixtures" / "pdfs"
EXPECTED = ROOT / "tests" / "fixtures" / "expected"
TESTFORMS = EXPECTED / "testforms"
CONFIGS = ROOT / "sample_configs"

TESTFORM_PDFS = ["test.pdf", "test10.pdf", "test14.pdf", "t15.pdf"]


def render_row(pdf: Path, config_name: str) -> list[str]:
    """Process a single-page PDF and return its CLI-style output row."""
    config = Form.model_validate_json((CONFIGS / config_name).read_text())
    with tempfile.TemporaryDirectory() as out, tempfile.TemporaryDirectory() as dbg:
        pages = read_images(pdf, convert_image=False)
        row = process_form(
            config,
            np.array(pages[0]),
            output_dir=out,
            debug_dir=dbg,
            extra={"filename": pdf, "page_num": 1, "data": None, "data_key": ""},
        )
    return [str(cell) for cell in row]


def update_testforms() -> None:
    config_name = "config.json"
    config = Form.model_validate_json((CONFIGS / config_name).read_text())
    header = config.get_header()
    TESTFORMS.mkdir(parents=True, exist_ok=True)
    for name in TESTFORM_PDFS:
        row = render_row(PDFS / name, config_name)
        assert len(row) == len(header), (name, len(row), len(header))
        out = TESTFORMS / f"{Path(name).stem}.csv"
        with out.open("w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(header)
            writer.writerow(row)
        print(f"wrote {out.relative_to(ROOT)}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--diff",
        action="store_true",
        help="only report the generated rows; do not write files",
    )
    args = parser.parse_args(argv)

    if args.diff:
        for name in TESTFORM_PDFS:
            row = render_row(PDFS / name, "config.json")
            print(f"{name}: {row[0]} -> {','.join(row[1:])}")
        return 0

    update_testforms()
    return 0


if __name__ == "__main__":
    sys.exit(main())
