"""Unit tests for the pydantic models in ``omr_diad.form``.

Valid cases are taken from the real files in ``sample_configs/``. Invalid
cases are built by deep-copying one of those configs and mutating it, so no
broken fixture files need to be committed.
"""

import copy
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from omr_diad.form import (
    Barcode,
    BarcodesSegment,
    BlockOrientation,
    BlockType,
    Form,
    ItemBlock,
    OutputFormat,
    SegmentType,
    Striped,
    TimingMarksSegment,
)

SAMPLES = Path(__file__).resolve().parents[1] / "sample_configs"

# Sample configs whose ``form_id`` is a barcode and whose single segment is a
# barcodes segment.
BARCODE_CONFIGS = [
    "config_formreturn.json",
    "config_formreturn_diad.json",
    "config_formreturn_potencial.json",
]
# Sample config whose ``form_id`` is a filled item block and whose segment only
# carries timing marks.
ITEMBLOCK_CONFIG = "config.json"
ALL_CONFIGS = BARCODE_CONFIGS + [ITEMBLOCK_CONFIG]


def load_sample(name: str) -> dict:
    """Load a sample config as a plain dict."""
    return json.loads((SAMPLES / name).read_text())


def copy_sample(name: str) -> dict:
    """Deep copy a sample config so tests can mutate it safely."""
    return copy.deepcopy(load_sample(name))


# ---------------------------------------------------------------------------
# Valid configs
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("name", ALL_CONFIGS)
def test_valid_configs_load(name):
    config = Form.model_validate_json((SAMPLES / name).read_text())

    assert isinstance(config, Form)
    assert config.name
    assert isinstance(config.page_size, tuple) and len(config.page_size) == 2
    assert config.segments

    if name in BARCODE_CONFIGS:
        assert isinstance(config.form_id, Barcode)
        assert isinstance(config.segments[0], BarcodesSegment)
    else:
        assert isinstance(config.form_id, ItemBlock)
        assert isinstance(config.segments[0], TimingMarksSegment)


def test_parsed_values(subtests):
    with subtests.test("DIAD itemblock config"):
        config = Form.model_validate_json((SAMPLES / ITEMBLOCK_CONFIG).read_text())
        assert config.page_size == (1240, 874)
        assert config.threshold == 0.1
        segment = config.segments[0]
        assert isinstance(segment, TimingMarksSegment)
        assert segment.timing_marks.count == 44
        assert segment.position == (80, 30)
        assert segment.size == (1100, 814)
        assert len(segment.item_blocks) == 3
        last_block = segment.item_blocks[-1]
        assert last_block.nrows == 16
        assert last_block.nopts == 4
        assert last_block.labels == (61, 76)
        assert last_block.bubble_labels == ["A", "B", "C", "D"]

    with subtests.test("FormReturn barcode config"):
        config = Form.model_validate_json((SAMPLES / BARCODE_CONFIGS[0]).read_text())
        assert config.page_size == (1190, 1684)
        assert config.threshold == 0.4  # default, not in the file
        segment = config.segments[0]
        assert isinstance(segment, BarcodesSegment)
        assert segment.bottom_left.text == "02"
        assert segment.top_right.text == "01"
        assert len(segment.item_blocks) == 4
        assert segment.item_blocks[0].nopts == 5

    with subtests.test("label_prefix is parsed"):
        config = Form.model_validate_json(
            (SAMPLES / "config_formreturn_potencial.json").read_text()
        )
        assert config.segments[0].item_blocks[0].label_prefix == "preg"


# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------


def test_form_defaults():
    config = Form.model_validate(
        {
            "name": "minimal",
            "page_size": [100, 200],
            "segments": [],
            "form_id": {"text": "", "position": [0, 0], "size": [0, 0]},
        }
    )
    assert config.contrast == 0
    assert config.brightness == 0
    assert config.threshold == 0.4
    assert config.luminance is None


def test_itemblock_defaults():
    block = ItemBlock.model_validate(
        {
            "position": [1, 2],
            "nrows": 3,
            "nopts": 4,
            "item_size": [5, 6],
            "bubble_size": [7, 8],
        }
    )
    assert block.orientation is BlockOrientation.HORIZONTAL
    assert block.block_type is BlockType.MCQ
    assert block.label_prefix == "item"
    assert block.labels is None
    assert block.bubble_labels is None
    assert block.color == "#85c8ff"
    assert block.opacity == 0.5
    assert block.striped is None


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


def test_enum_values(subtests):
    with subtests.test("OutputFormat"):
        assert OutputFormat.CSV.value == "csv"
        assert OutputFormat.DAT.value == "dat"
    with subtests.test("Striped"):
        assert Striped.EVEN.value == "even"
        assert Striped.ODD.value == "odd"
    with subtests.test("BlockOrientation"):
        assert BlockOrientation.HORIZONTAL.value == "horizontal"
        assert BlockOrientation.VERTICAL.value == "vertical"
    with subtests.test("BlockType"):
        assert BlockType.MCQ.value == "MCQ"
        assert BlockType.BIN.value == "BIN"
    with subtests.test("SegmentType"):
        assert SegmentType.BARCODES.value == "barcodes"
        assert SegmentType.TIMING_MARKS.value == "timing marks"


def test_enum_is_parsed_from_string(subtests):
    with subtests.test("orientation"):
        block = ItemBlock.model_validate(
            {
                "position": [0, 0],
                "nrows": 1,
                "nopts": 1,
                "item_size": [1, 1],
                "bubble_size": [1, 1],
                "orientation": "vertical",
                "striped": "odd",
            }
        )
        assert block.orientation is BlockOrientation.VERTICAL
        assert block.striped is Striped.ODD

    with subtests.test("invalid orientation"):
        with pytest.raises(ValidationError) as exc:
            ItemBlock.model_validate(
                {
                    "position": [0, 0],
                    "nrows": 1,
                    "nopts": 1,
                    "item_size": [1, 1],
                    "bubble_size": [1, 1],
                    "orientation": "diagonal",
                }
            )
        errors = exc.value.errors()
        assert any(
            e["type"] == "enum" and e["loc"] == ("orientation",) for e in errors
        )


# ---------------------------------------------------------------------------
# Behavior of the model classes
# ---------------------------------------------------------------------------


def test_extra_fields_are_ignored():
    config = copy_sample(ITEMBLOCK_CONFIG)
    config["bogus"] = 123
    config["segments"][0]["item_blocks"][0]["also_bogus"] = "x"

    validated = Form.model_validate(config)

    assert validated.name == config["name"]
    assert not hasattr(validated, "bogus")
    assert not hasattr(validated.segments[0].item_blocks[0], "also_bogus")


def test_segment_type_is_not_tied_to_segment_class(subtests):
    """``segment_type`` is a plain enum field, so pydantic does not require it
    to match the concrete ``Segment`` subclass that wins the union."""
    with subtests.test("barcodes-shaped segment labelled as timing marks"):
        config = copy_sample(BARCODE_CONFIGS[0])
        config["segments"][0]["segment_type"] = "timing marks"
        validated = Form.model_validate(config)
        segment = validated.segments[0]
        assert isinstance(segment, BarcodesSegment)
        assert segment.segment_type is SegmentType.TIMING_MARKS

    with subtests.test("timing-marks-shaped segment labelled as barcodes"):
        config = copy_sample(ITEMBLOCK_CONFIG)
        config["segments"][0]["segment_type"] = "barcodes"
        validated = Form.model_validate(config)
        segment = validated.segments[0]
        assert isinstance(segment, TimingMarksSegment)
        assert segment.segment_type is SegmentType.BARCODES


def test_get_header(subtests):
    config = Form.model_validate_json((SAMPLES / ITEMBLOCK_CONFIG).read_text())
    with subtests.test("with explicit labels"):
        assert config.get_header() == ["ID"] + [f"item{i}" for i in range(1, 77)]

    with subtests.test("labels fall back to nrows"):
        for segment in config.segments:
            for block in segment.item_blocks:
                block.labels = None
        header = config.get_header()
        assert header == ["ID"] + [f"item{i}" for i in range(1, 31)] * 2 + [
            f"item{i}" for i in range(1, 17)
        ]

    with subtests.test("label_prefix is used"):
        config = Form.model_validate_json(
            (SAMPLES / "config_formreturn_potencial.json").read_text()
        )
        header = config.get_header()
        assert header[0] == "ID"
        assert header[1] == "preg1"
        assert header[-1] == "preg96"


def test_get_fragment_positions(subtests):
    config = Form.model_validate_json((SAMPLES / ITEMBLOCK_CONFIG).read_text())
    positions = config.get_fragment_positions()

    with subtests.test("one entry per item"):
        assert len(positions) == 76

    with subtests.test("first and last of first block"):
        assert positions["item1"] == (579, 43, 100, 25)
        assert positions["item30"] == (579, 768, 100, 25)

    with subtests.test("positions of the other blocks"):
        assert positions["item31"] == (807, 43, 100, 25)
        assert positions["item61"] == (1061, 43, 100, 25)
        assert positions["item76"] == (1061, 418, 100, 25)


# ---------------------------------------------------------------------------
# Invalid cases
# ---------------------------------------------------------------------------


def test_missing_required_fields(subtests):
    with subtests.test("empty Form"):
        with pytest.raises(ValidationError) as exc:
            Form.model_validate({})
        locs = {e["loc"][0] for e in exc.value.errors()}
        assert {"name", "page_size", "segments", "form_id"} <= locs

    with subtests.test("Form without segments"):
        config = copy_sample(ITEMBLOCK_CONFIG)
        del config["segments"]
        with pytest.raises(ValidationError) as exc:
            Form.model_validate(config)
        assert any(
            e["type"] == "missing" and e["loc"] == ("segments",)
            for e in exc.value.errors()
        )

    with subtests.test("ItemBlock without position"):
        with pytest.raises(ValidationError) as exc:
            ItemBlock.model_validate(
                {"nrows": 1, "nopts": 1, "item_size": [1, 1], "bubble_size": [1, 1]}
            )
        assert any(
            e["type"] == "missing" and e["loc"] == ("position",)
            for e in exc.value.errors()
        )

    with subtests.test("Barcode without text"):
        with pytest.raises(ValidationError) as exc:
            Barcode.model_validate({"position": [0, 0], "size": [1, 1]})
        assert any(
            e["type"] == "missing" and e["loc"] == ("text",)
            for e in exc.value.errors()
        )

    with subtests.test("BarcodesSegment without its barcodes"):
        config = copy_sample(BARCODE_CONFIGS[0])
        del config["segments"][0]["bottom_left"]
        del config["segments"][0]["top_right"]
        with pytest.raises(ValidationError) as exc:
            Form.model_validate(config)
        types = {e["type"] for e in exc.value.errors()}
        assert "missing" in types


@pytest.mark.parametrize(
    "change,loc,error_type",
    [
        ("page_size", ("page_size",), "too_long"),
        ("threshold", ("threshold",), "float_parsing"),
    ],
)
def test_form_wrong_types_rejected(change, loc, error_type):
    config = copy_sample(ITEMBLOCK_CONFIG)
    if change == "page_size":
        config["page_size"] = [1, 2, 3]
    else:
        config["threshold"] = "not-a-number"

    with pytest.raises(ValidationError) as exc:
        Form.model_validate(config)

    assert any(
        e["type"] == error_type and e["loc"] == loc for e in exc.value.errors()
    )


@pytest.mark.parametrize(
    "field,value,loc",
    [
        ("position", ["a", "b"], ("position", 0)),
        ("nrows", "abc", ("nrows",)),
        ("nopts", None, ("nopts",)),
    ],
)
def test_itemblock_wrong_types_rejected(field, value, loc):
    data = {
        "position": [0, 0],
        "nrows": 1,
        "nopts": 1,
        "item_size": [1, 1],
        "bubble_size": [1, 1],
    }
    data[field] = value

    with pytest.raises(ValidationError) as exc:
        ItemBlock.model_validate(data)

    errors = exc.value.errors()
    assert any(e["loc"] == loc and e["type"] != "missing" for e in errors)


def test_union_without_matching_branch_rejected(subtests):
    with subtests.test("form_id is neither barcode nor itemblock"):
        config = copy_sample(ITEMBLOCK_CONFIG)
        config["form_id"] = {"foo": 1}
        with pytest.raises(ValidationError) as exc:
            Form.model_validate(config)
        errors = exc.value.errors()
        assert errors
        assert all(e["loc"][0] == "form_id" for e in errors)

    with subtests.test("segment is neither barcodes nor timing marks"):
        config = copy_sample(BARCODE_CONFIGS[0])
        del config["segments"][0]["bottom_left"]
        del config["segments"][0]["top_right"]
        with pytest.raises(ValidationError) as exc:
            Form.model_validate(config)
        errors = exc.value.errors()
        assert errors
        assert all(e["loc"][0] == "segments" for e in errors)


def test_invalid_segment_type_rejected():
    config = copy_sample(BARCODE_CONFIGS[0])
    config["segments"][0]["segment_type"] = "nonsense"

    with pytest.raises(ValidationError) as exc:
        Form.model_validate(config)

    errors = exc.value.errors()
    assert any(
        e["type"] == "enum"
        and e["loc"] == ("segments", 0, "BarcodesSegment", "segment_type")
        for e in errors
    )
