"""E2E: CLI argument handling and error reporting."""

from tests.conftest import IDS, PDFS, SAMPLES, cli_dirs, run_cli


def test_help_lists_the_process_command():
    result = run_cli("--help")

    assert result.returncode == 0
    assert "process" in result.stdout


def test_missing_config_file_is_rejected(tmp_path):
    out, debug, error = cli_dirs(tmp_path)
    result = run_cli(
        "process",
        PDFS / "test.pdf",
        "--config-file",
        tmp_path / "missing.json",
        "--out-dir",
        out,
        "--debug-dir",
        debug,
        "--error-dir",
        error,
    )

    assert result.returncode != 0
    assert "does not exist" in (result.stdout + result.stderr).lower()


def test_unknown_data_id_fails(tmp_path):
    out, debug, error = cli_dirs(tmp_path)
    result = run_cli(
        "process",
        PDFS / "L309.pdf",
        "--config-file",
        SAMPLES / "config_formreturn_diad.json",
        "--data-file",
        IDS / "ars271c2_datos.csv",
        "--data-id",
        "NOT_A_COLUMN",
        "--out-dir",
        out,
        "--debug-dir",
        debug,
        "--error-dir",
        error,
        "--single-process",
    )

    assert result.returncode != 0
    assert "NOT_A_COLUMN" in (result.stdout + result.stderr)
