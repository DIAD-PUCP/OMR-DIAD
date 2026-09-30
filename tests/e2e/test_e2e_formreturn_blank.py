"""E2E: FormReturn DIAD forms processed through the CLI.

``calibracion.pdf`` is a blank calibration scan; its output is compared against
``tests/fixtures/expected/test2.csv`` (50 rows, all answers blank). This is the
only case that needs poppler/pdf2image.
"""

from tests.comparison import compare_sorted
from tests.conftest import (
    EXPECTED,
    PDFS,
    SAMPLES,
    cli_dirs,
    index_rows,
    item_labels,
    load_config,
    parse_csv,
    read_rows,
    requires_poppler,
    run_cli,
)


@requires_poppler
def test_formreturn_blank_calibration_end_to_end(tmp_path):
    out, debug, error = cli_dirs(tmp_path)
    result = run_cli(
        "process",
        PDFS / "calibracion.pdf",
        "--config-file",
        SAMPLES / "config_formreturn_diad.json",
        "--out-dir",
        out,
        "--debug-dir",
        debug,
        "--error-dir",
        error,
        "--convert",
        "--single-process",
    )
    assert result.returncode == 0, result.stderr

    rows = parse_csv(result.stdout)
    labels = item_labels(load_config("config_formreturn_diad.json"))
    assert rows[0] == ["ID"] + labels
    assert len(rows) - 1 == 50

    actual = index_rows(rows[1:], labels)
    golden = index_rows(read_rows(EXPECTED / "test2.csv"), labels)
    compare_sorted(actual, golden, max_diffs=0).raise_for_status()
