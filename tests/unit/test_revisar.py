"""Unit tests for the Streamlit review helpers in ``omr_diad.revisar``.

``revisar`` is a Streamlit script, so the session state is replaced with a
plain dictionary before exercising ``procesar_cambios``.
"""

import csv
from pathlib import Path

import pandas as pd

import omr_diad.revisar as revisar
from omr_diad.revisar import get_scans, procesar_cambios


def test_get_scans(subtests):
    with subtests.test("only .png files are collected"):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "00001 (E201.pdf 1).png").write_bytes(b"x")
            (root / "00002 (E201.pdf 2).png").write_bytes(b"x")
            (root / "notes.txt").write_text("ignored")
            scans = get_scans(root)

        assert set(scans) == {"00001", "00002"}
        assert all(path.suffix == ".png" for path in scans.values())

    with subtests.test("the first five characters are the exam id"):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "05187-extra.png").write_bytes(b"x")
            scans = get_scans(root)

        assert set(scans) == {"05187"}


def test_procesar_cambios(monkeypatch):
    monkeypatch.setattr(
        revisar.st,
        "session_state",
        {"correcciones": {"0001": {"item1": "A", "item2": "D"}}},
    )
    original = pd.DataFrame(
        {"EXAMEN": ["0001", "0002"], "item1": ["B", "C"], "item2": ["B", "C"]}
    )

    out = procesar_cambios(original)
    rows = list(csv.reader(out.splitlines()))

    assert rows[0] == ["EXAMEN", "item1", "item2"]
    assert rows[1] == ["0001", "A", "D"]
    assert rows[2] == ["0002", "C", "C"]
    # The original frame must not be mutated.
    assert original.loc[original["EXAMEN"] == "0001", "item1"].item() == "B"
