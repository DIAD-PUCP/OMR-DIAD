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


def test_form_diad():
    assert True
