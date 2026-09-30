"""E2E: the default multiprocessing path must match ``--single-process``."""

from tests.conftest import PDFS, SAMPLES, parse_csv, run_cli


def _run(pdf, out, debug, error, single, tmp_path):
    import shutil

    for directory in (out, debug, error):
        shutil.rmtree(directory, ignore_errors=True)
        directory.mkdir(parents=True)
    args = [
        "process",
        str(pdf),
        "--config-file",
        str(SAMPLES / "config.json"),
        "--out-dir",
        str(out),
        "--debug-dir",
        str(debug),
        "--error-dir",
        str(error),
    ]
    if single:
        args.append("--single-process")
    return run_cli(*args)


def test_multiprocessing_matches_single_process(tmp_path):
    pdf = PDFS / "test14.pdf"

    single = _run(
        pdf,
        tmp_path / "s_out",
        tmp_path / "s_dbg",
        tmp_path / "s_err",
        single=True,
        tmp_path=tmp_path,
    )
    pooled = _run(
        pdf,
        tmp_path / "p_out",
        tmp_path / "p_dbg",
        tmp_path / "p_err",
        single=False,
        tmp_path=tmp_path,
    )

    assert single.returncode == 0, single.stderr
    assert pooled.returncode == 0, pooled.stderr
    assert parse_csv(single.stdout) == parse_csv(pooled.stdout)
