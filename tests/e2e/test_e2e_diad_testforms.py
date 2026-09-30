"""E2E: single-page DIAD samples processed through the CLI.

Each PDF has its own committed golden under
``tests/fixtures/expected/testforms/`` (regenerate with
``python -m tests.tools.update_goldens``).
"""

from pathlib import Path

import pytest

from tests.comparison import compare_sorted
from tests.conftest import (
    PDFS,
    SAMPLES,
    TESTFORMS,
    cli_dirs,
    index_rows,
    item_labels,
    load_config,
    parse_csv,
    read_golden,
    run_cli,
)

TESTFORM_PDFS = ["test.pdf", "test10.pdf", "test14.pdf", "t15.pdf"]


@pytest.mark.parametrize("name", TESTFORM_PDFS)
def test_diad_single_page_sample(name, tmp_path):
    out, debug, error = cli_dirs(tmp_path)
    result = run_cli(
        "process",
        PDFS / name,
        "--config-file",
        SAMPLES / "config.json",
        "--out-dir",
        out,
        "--debug-dir",
        debug,
        "--error-dir",
        error,
        "--single-process",
    )
    assert result.returncode == 0, result.stderr

    rows = parse_csv(result.stdout)
    labels = item_labels(load_config("config.json"))
    assert rows[0] == ["ID"] + labels

    actual = index_rows(rows[1:], labels)
    golden = read_golden(TESTFORMS / f"{Path(name).stem}.csv", "ID")
    expected = {
        key: {label: row[label] for label in labels} for key, row in golden.items()
    }
    compare_sorted(actual, expected, max_diffs=0).raise_for_status()
