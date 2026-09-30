"""E2E: DIAD timing-mark forms processed through the CLI.

Baseline: ``tests/fixtures/expected/test3.csv`` (16 pages, ItemBlock form id,
deterministic pypdf embedded-image extraction).
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
    run_cli,
)


def test_diad_timing_marks_end_to_end(tmp_path):
    out, debug, error = cli_dirs(tmp_path)
    result = run_cli(
        "process",
        PDFS / "test3.pdf",
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
    assert len(rows) - 1 == 16

    actual = index_rows(rows[1:], labels)
    golden = index_rows(read_rows(EXPECTED / "test3.csv"), labels)
    # Two cells are allowlisted as partial multi-mark detections (see
    # tests/fixtures/known_diffs.json); the ceiling bounds everything else.
    compare_sorted(actual, golden, max_diffs=2).raise_for_status()
