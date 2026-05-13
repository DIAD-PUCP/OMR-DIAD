from src.form import Barcode, Form, ItemBlock


def test_config_load(subtests):
    with open("../sample_configs/config.json") as f:
        json_config = f.read()
        with subtests.test("DIAD config load"):
            config = Form.model_validate_json(json_config)
            assert isinstance(config.form_id, ItemBlock)

    with open("../sample_configs/config_formreturn_diad.json") as f:
        json_config = f.read()
        with subtests.test("DIAD FormReturn config load"):
            config = Form.model_validate_json(json_config)
            assert isinstance(config.form_id, Barcode)

    with open("../sample_configs/config_formreturn.json") as f:
        json_config = f.read()
        with subtests.test("DIAD FormReturn sample config load"):
            config = Form.model_validate_json(json_config)
            assert isinstance(config.form_id, Barcode)


def test_config_header(subtests):
    with open("../sample_configs/config.json") as f:
        json_config = f.read()
        config = Form.model_validate_json(json_config)
        with subtests.test("DIAD config header"):
            header = config.get_header()
            assert header == ["ID"] + [f"item{i}" for i in range(1, 77)]

        for i, seg in enumerate(config.segments):
            for j, _ in enumerate(seg.item_blocks):
                config.segments[i].item_blocks[j].labels = None
        with subtests.test("DIAD config header without labels"):
            header = config.get_header()
            assert header == ["ID"] + [f"item{i}" for i in range(1, 31)] * 2 + [
                f"item{i}" for i in range(1, 17)
            ]


def test_form_diad():
    assert True
