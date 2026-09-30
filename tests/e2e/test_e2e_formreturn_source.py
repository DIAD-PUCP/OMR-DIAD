"""E2E: FormReturn DIAD forms joined with a source-data file.

``L309.pdf`` (8 pages) is processed with ``config_formreturn_diad.json`` and
``ars271c2_datos.csv``; the rows are verified against the matching ``CODIGO``
entries of ``ars271c2.csv``.

``F1603093`` carries five blank-vs-answer differences on trailing items that
the answer-presence rule tolerates; ``max_diffs`` is the hard ceiling for the
whole run.
"""

from tests.comparison import compare_rows
from tests.conftest import (
    EXPECTED,
    IDS,
    PDFS,
    SAMPLES,
    cli_dirs,
    item_labels,
    load_config,
    parse_csv,
    read_golden,
    run_cli,
)

MAX_DIFFS = 10


def test_formreturn_source_join_end_to_end(tmp_path):
    out, debug, error = cli_dirs(tmp_path)
    result = run_cli(
        "process",
        PDFS / "L309.pdf",
        "--config-file",
        SAMPLES / "config_formreturn_diad.json",
        "--data-file",
        IDS / "ars271c2_datos.csv",
        "--data-id",
        "form_id",
        "--data-key",
        "EXAMEN",
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
    items = item_labels(load_config("config_formreturn_diad.json"))
    golden = read_golden(EXPECTED / "ars271c2.csv", "CODIGO")
    data_cols = list(next(iter(golden.values())))[:11]

    assert rows[0] == data_cols + items
    assert len(rows) - 1 == 8

    pairs = []
    for row in rows[1:]:
        key = row[0]
        assert key in golden, f"unexpected form {key}"
        assert dict(zip(data_cols, row[:11])) == {col: golden[key][col] for col in data_cols}
        actual_items = dict(zip(items, row[11:]))
        expected_items = {label: golden[key][label] for label in items}
        pairs.append((key, actual_items, expected_items))

    compare_rows(pairs, max_diffs=MAX_DIFFS).raise_for_status()
