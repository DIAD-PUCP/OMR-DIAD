# OMR-DIAD test suite

The tests are split into three stages, each mapped to a folder and a pytest
marker (applied automatically by `conftest.py`, the modules themselves carry no
markers):

| Folder | Marker | What it covers |
|---|---|---|
| `tests/unit/` | `unit` | One function or model in isolation. Synthetic numpy arrays, temp files. Fast. |
| `tests/integration/` | `integration` | Several modules together: PDF reading, synthetic-form recognition, `process_form`, output formatting. |
| `tests/e2e/` | `e2e` | The real CLI (`python -m omr_diad.main process ...`) over committed scans, compared against goldens. |

`generate.py` is experimental and intentionally has no tests.

## Running

```bash
pytest                 # everything (uses the coverage addopts in pyproject)
pytest -m "not e2e"    # fast unit + integration
pytest -m unit
pytest -m integration
pytest -m e2e
```

The `e2e` case for `calibracion.pdf` needs poppler (`pdftoppm`) and is skipped
automatically when it is missing; the rest use the deterministic pypdf
embedded-image path.

## Golden comparison

`tests/comparison.py` implements the tolerant strategy:

1. **Normalize** every cell (`" "` and `""` mean the same, whitespace trimmed).
2. **Answer-presence tolerance** (default): a cell may differ only when one side
   is blank; a real "letter vs different letter" swap is a hard failure.
3. **Allowlist**: `tests/fixtures/known_diffs.json` lists explicit
   `(row_id, item_label)` pairs that may differ, with a reason.
4. **Hard ceiling**: the total number of differing cells (tolerated included)
   may not exceed the `max_diffs` passed by each test.

Rows produced with a `--data-file` are matched to the golden by `CODIGO`; rows
without one are matched by their form id.

## Fixtures

Committed under `tests/fixtures/` so the suite runs on a fresh clone:

- `pdfs/` – the scans used by the E2E cases.
- `ids/` – source-data files passed with `--data-file`.
- `expected/` – goldens. `ars271c2.csv` and `LUCET262_pot_formreturn.csv` are
  full process exports; the tests compare the subset of rows produced by each
  PDF. `test2.csv` (blank calibration) and `test3.csv` are legacy goldens.
- `expected/testforms/` – one single-page golden per DIAD sample.

Regenerate the single-page goldens after an intentional detection change:

```bash
python -m tests.tools.update_goldens          # write
python -m tests.tools.update_goldens --diff   # inspect only
```

## E2E cases

| PDF | Config | Data file | Golden |
|---|---|---|---|
| `test3.pdf` | `config.json` | – | `expected/test3.csv` |
| `calibracion.pdf` | `config_formreturn_diad.json` | – | `expected/test2.csv` (blank) |
| `L309.pdf` | `config_formreturn_diad.json` | `ars271c2_datos.csv` | `expected/ars271c2.csv` (subset) |
| `E105.pdf` | `config_formreturn_potencial.json` | `LUCETPOT_id.csv` | `expected/LUCET262_pot_formreturn.csv` (subset) |
| `test.pdf`, `test10.pdf`, `test14.pdf`, `t15.pdf` | `config.json` | – | `expected/testforms/*.csv` |
