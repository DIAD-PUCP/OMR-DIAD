"""Unit tests for the form-id helpers in ``omr_diad.form_id``."""

import numpy as np
import pytest

from omr_diad.form import Form
from omr_diad.form_id import find_barcode_id, find_itemblock_id
from tests.conftest import SAMPLES


@pytest.fixture
def barcode_config() -> Form:
    return Form.model_validate_json(
        (SAMPLES / "config_formreturn_diad.json").read_text()
    )


def test_find_barcode_id_rejects_non_barcode_config(config):
    with pytest.raises(RuntimeError, match="barcode_id"):
        find_barcode_id(config, np.zeros((10, 10, 3), dtype=np.uint8))


def test_find_barcode_id_without_a_barcode_raises(barcode_config):
    blank = np.full((200, 200, 3), 255, dtype=np.uint8)
    with pytest.raises(RuntimeError, match="not found"):
        find_barcode_id(barcode_config, blank)


def test_find_itemblock_id_rejects_non_itemblock_config(barcode_config):
    with pytest.raises(RuntimeError, match="ItemBlock"):
        find_itemblock_id(barcode_config, np.zeros((10, 10, 3), dtype=np.uint8))
