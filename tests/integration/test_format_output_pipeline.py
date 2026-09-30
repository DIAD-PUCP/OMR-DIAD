"""Integration test composing ``read_source_data`` + ``Form.get_header`` +
``format_output``, which is how the CLI builds its CSV/DAT output.
"""

from omr_diad.form import OutputFormat
from omr_diad.processing import format_output, read_source_data
from tests.conftest import IDS


def test_source_data_header_and_rows(config):
    source = read_source_data(IDS / "ars271c2_datos.csv", "form_id")

    out = format_output(
        config,
        [["F1597601", "NAME", "ARCH", "A", "B"]],
        OutputFormat.CSV,
        use_header=True,
        source_data=source,
    )
    header, _, body = out.partition("\n")

    # 11 source columns without form_id + 76 items.
    assert header.startswith('"CODIGO","NOMBRE COMPLETO"')
    assert header.endswith('"item76"')
    assert len(header.split(",")) == 87
    assert body.startswith('"F1597601","NAME","ARCH","A","B"')


def test_dat_output_keeps_one_character_per_item(config):
    out = format_output(
        config,
        [["28883", "A", "B,C", "", "D"]],
        OutputFormat.DAT,
        use_header=False,
    )

    # Multi-character answers collapse to "*" and blanks stay blank.
    assert out == "28883A*D"
