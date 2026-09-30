"""Shared paths, fixtures and helpers for the OMR-DIAD test suite."""

from __future__ import annotations

import csv
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from omr_diad.form import Form

ROOT = Path(__file__).resolve().parents[1]
# Make ``tests`` importable as a package regardless of the import mode.
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

SAMPLES = ROOT / "sample_configs"
FIXTURES = Path(__file__).resolve().parent / "fixtures"
PDFS = FIXTURES / "pdfs"
EXPECTED = FIXTURES / "expected"
TESTFORMS = EXPECTED / "testforms"
IDS = FIXTURES / "ids"

# Configs whose ``form_id`` is a barcode.
BARCODE_CONFIGS = [
    "config_formreturn.json",
    "config_formreturn_diad.json",
    "config_formreturn_potencial.json",
]
ITEMBLOCK_CONFIG = "config.json"

HAS_POPPLER = shutil.which("pdftoppm") is not None
requires_poppler = pytest.mark.skipif(
    not HAS_POPPLER, reason="pdf2image requires poppler (pdftoppm) to be installed"
)


def pytest_configure(config: pytest.Config) -> None:
    for marker, description in (
        ("unit", "fast, isolated unit test"),
        ("integration", "exercises several modules together"),
        ("e2e", "full CLI pipeline on real scans"),
    ):
        config.addinivalue_line("markers", f"{marker}: {description}")


# Which test folder maps to which stage marker. Applied automatically so the
# test modules themselves stay untouched.
_STAGE_DIRS = (
    ("unit", "tests/unit/"),
    ("integration", "tests/integration/"),
    ("e2e", "tests/e2e/"),
)


def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    for item in items:
        posix = Path(str(item.fspath)).as_posix()
        for marker, prefix in _STAGE_DIRS:
            if f"/{prefix}" in f"/{posix}":
                item.add_marker(getattr(pytest.mark, marker))
                break


def load_config(name: str) -> Form:
    return Form.model_validate_json((SAMPLES / name).read_text())


@pytest.fixture
def config() -> Form:
    """The DIAD item-block config (timing marks, 76 items)."""
    return load_config(ITEMBLOCK_CONFIG)


@pytest.fixture
def barcode_config() -> Form:
    """The DIAD FormReturn config (barcode id, 76 items)."""
    return load_config("config_formreturn_diad.json")


@pytest.fixture
def formreturn_config() -> Form:
    """The standard FormReturn config (barcode id, 100 items)."""
    return load_config("config_formreturn.json")


@pytest.fixture
def potencial_config() -> Form:
    """The potential-process config (barcode id, 96 ``preg`` items)."""
    return load_config("config_formreturn_potencial.json")


def run_cli(*args: object, cwd: Path | None = None) -> subprocess.CompletedProcess:
    """Run ``python -m omr_diad.main`` with the given arguments.

    The real CLI is used (rather than calling the module functions) so the
    tests exercise argument parsing, multiprocessing and file handling too.
    """
    cmd = [sys.executable, "-m", "omr_diad.main", *(str(a) for a in args)]
    return subprocess.run(
        cmd,
        cwd=cwd or ROOT,
        capture_output=True,
        text=True,
    )


def parse_csv(text: str) -> list[list[str]]:
    """Parse CSV printed by the CLI, ignoring blank lines."""
    rows = [row for row in csv.reader(text.splitlines()) if row]
    return rows


def read_rows(path: Path) -> list[list[str]]:
    """Read a headerless golden file (``tests/test2.csv`` style)."""
    with path.open() as f:
        return [row for row in csv.reader(f) if row]


def read_golden(path: Path, key: str) -> dict[str, dict[str, str]]:
    """Read a golden file with a header, keyed by ``key``."""
    with path.open() as f:
        reader = csv.DictReader(f)
        return {row[key]: row for row in reader}


def item_labels(form: Form) -> list[str]:
    return form.get_header()[1:]


def index_rows(
    rows: list[list[str]], labels: list[str]
) -> dict[str, dict[str, str]]:
    """Turn ``[[id, *items], ...]`` rows into ``{id: {label: value}}``."""
    return {row[0]: dict(zip(labels, row[1:])) for row in rows}


def cli_dirs(tmp_path: Path) -> tuple[Path, Path, Path]:
    out = tmp_path / "out"
    debug = tmp_path / "debug"
    error = tmp_path / "error"
    for d in (out, debug, error):
        d.mkdir()
    return out, debug, error
