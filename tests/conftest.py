"""Shared paths and fixtures for the test suite."""

from pathlib import Path

import pytest

from omr_diad.form import Form

SAMPLES = Path(__file__).resolve().parents[1] / "sample_configs"


@pytest.fixture
def config() -> Form:
    """The DIAD item-block config used across the unit tests."""
    return Form.model_validate_json((SAMPLES / "config.json").read_text())
