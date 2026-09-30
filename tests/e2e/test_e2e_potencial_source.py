"""E2E: potential-process forms joined with a source-data file.

``E105.pdf`` (3 pages) is processed with ``config_formreturn_potencial.json``
(the 96-item ``preg`` format) and ``LUCETPOT_id.csv``; the rows are verified
against the matching ``CODIGO`` entries of ``LUCET262_pot_formreturn.csv``.
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


def test_potencial_source_join_end_to_end(tmp_path):
    out, debug, error = cli_dirs(tmp_path)
    result = run_cli(
        "process",
        PDFS / "E105.pdf",
        "--config-file",
        SAMPLES / "config_formreturn_potencial.json",
        "--data-file",
        IDS / "LUCETPOT_id.csv",
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
    items = item_labels(load_config("config_formreturn_potencial.json"))
    golden = read_golden(EXPECTED / "LUCET262_pot_formreturn.csv", "CODIGO")
    data_cols = list(next(iter(golden.values())))[:11]

    assert rows[0] == data_cols + items
    assert len(rows) - 1 == 3

    pairs = []
    for row in rows[1:]:
        key = row[0]
        assert key in golden, f"unexpected form {key}"
        assert dict(zip(data_cols, row[:11])) == {col: golden[key][col] for col in data_cols}
        actual_items = dict(zip(items, row[11:]))
        expected_items = {label: golden[key][label] for label in items}
        pairs.append((key, actual_items, expected_items))

    compare_rows(pairs, max_diffs=0).raise_for_status()
