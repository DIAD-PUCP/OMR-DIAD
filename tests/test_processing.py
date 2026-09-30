"""Unit tests for the pure helpers in ``omr_diad.processing``."""

from pathlib import Path

import numpy as np
import pytest

from omr_diad.form import Form, OutputFormat
from omr_diad.processing import (
    apply_brightness_contrast,
    format_output,
    read_source_data,
)

SAMPLES = Path(__file__).resolve().parents[1] / "sample_configs"


@pytest.fixture
def config() -> Form:
    return Form.model_validate_json((SAMPLES / "config.json").read_text())


def test_format_output_csv(config, subtests):
    results = [["id1", "A", "B"], ["id2", "C", ""]]

    with subtests.test("rows without header"):
        out = format_output(config, results, OutputFormat.CSV, use_header=False)
        assert out == '"id1","A","B"\n"id2","C",""'

    with subtests.test("header from the config"):
        out = format_output(config, results, OutputFormat.CSV, use_header=True)
        header, _, body = out.partition("\n")
        assert header.startswith('"ID","item1","item2"')
        assert len(header.split(",")) == 77  # ID + 76 items
        assert body == '"id1","A","B"\n"id2","C",""'

    with subtests.test("empty string and blank element"):
        # A single space is written as an empty quoted field; an empty string
        # is kept as-is (also resulting in an empty quoted field).
        out = format_output(config, [["id1", " ", ""]], OutputFormat.CSV, use_header=False)
        assert out == '"id1","",""'

    with subtests.test("rows are sorted"):
        out = format_output(
            config,
            [["id2", "A"], ["id1", "B"]],
            OutputFormat.CSV,
            use_header=False,
        )
        assert out == '"id1","B"\n"id2","A"'

    with subtests.test("source data columns are prepended"):
        source = {"k": {"form_id": "k", "EXAMEN": "E1", "NOMBRE": "N1"}}
        out = format_output(
            config, [["E1", "N1", "A"]], OutputFormat.CSV, source_data=source
        )
        header = out.partition("\n")[0]
        assert header.startswith('"EXAMEN","NOMBRE","item1"')
        assert len(header.split(",")) == 78  # 2 data cols + 76 items


def test_format_output_dat(config, subtests):
    with subtests.test("multi-character answers collapse to *"):
        out = format_output(config, [["id1", "AB", "C"]], OutputFormat.DAT)
        assert out == "id1*C"

    with subtests.test("single-character answers pass through"):
        out = format_output(config, [["id1", "A", "B"]], OutputFormat.DAT)
        assert out == "id1AB"

    with subtests.test("rows are sorted"):
        out = format_output(
            config, [["id2", "A"], ["id1", "B"]], OutputFormat.DAT
        )
        assert out == "id1B\nid2A"


def test_read_source_data(tmp_path):
    data_file = tmp_path / "data.csv"
    data_file.write_text("form_id,EXAMEN,NOMBRE\n0001,0001,ALICE\n0002,0002,BOB\n")

    result = read_source_data(data_file, "form_id")

    assert set(result) == {"0001", "0002"}
    assert result["0001"] == {"form_id": "0001", "EXAMEN": "0001", "NOMBRE": "ALICE"}
    assert result["0002"]["NOMBRE"] == "BOB"


def test_apply_brightness_contrast(subtests):
    img = np.tile(np.arange(64, dtype=np.uint8), (64, 1))
    rgb = np.stack([img, img, img], axis=-1)

    with subtests.test("zero adjustments returns an equal copy"):
        out = apply_brightness_contrast(rgb, brightness=0, contrast=0)
        assert out is not rgb
        assert out.shape == rgb.shape
        assert out.dtype == rgb.dtype
        assert np.array_equal(out, rgb)

    with subtests.test("non-zero adjustments keep the shape"):
        out = apply_brightness_contrast(rgb, brightness=30, contrast=20)
        assert out.shape == rgb.shape
        assert out.dtype == rgb.dtype
        assert not np.array_equal(out, rgb)
