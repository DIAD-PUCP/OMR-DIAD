import csv
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np

from omr_diad.form import Barcode, Form, ItemBlock
from omr_diad.main import proc_img, read_images


def test_config_load(subtests):
    with open("./sample_configs/config.json") as f:
        json_config = f.read()
        with subtests.test("DIAD config load"):
            config = Form.model_validate_json(json_config)
            assert isinstance(config.form_id, ItemBlock)

    with open("./sample_configs/config_formreturn_diad.json") as f:
        json_config = f.read()
        with subtests.test("DIAD FormReturn config load"):
            config = Form.model_validate_json(json_config)
            assert isinstance(config.form_id, Barcode)

    with open("./sample_configs/config_formreturn.json") as f:
        json_config = f.read()
        with subtests.test("DIAD FormReturn sample config load"):
            config = Form.model_validate_json(json_config)
            assert isinstance(config.form_id, Barcode)


def test_config_header(subtests):
    with open("./sample_configs/config.json") as f:
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


def test_form_diad(subtests):
    with open("./sample_configs/config.json") as f:
        json_config = f.read()
        config = Form.model_validate_json(json_config)
    with open("./tests/test3.csv") as csvfile:
        reader = csv.reader(csvfile)
        results = [row for row in reader]
    images = read_images(Path("./inputs/test3.pdf"), False)
    out_dir = TemporaryDirectory()
    debug_dir = TemporaryDirectory()
    error_dir = TemporaryDirectory()
    images = [
        (
            i,
            Path("test10.pdf"),
            config,
            np.array(img),
            out_dir.name,
            debug_dir.name,
            error_dir.name,
            None,
            "",
        )
        for i, img in enumerate(images)
    ]
    for data, result in zip(images, results):
        with subtests.test("DIAD test forms", name=f"test10.pdf ({data[0] + 1})"):
            res = proc_img(data)
            assert result == res


def test_formreturn_diad(subtests):
    with open("./sample_configs/config_formreturn_diad.json") as f:
        json_config = f.read()
        config = Form.model_validate_json(json_config)
    with open("./tests/test2.csv") as csvfile:
        reader = csv.reader(csvfile)
        results = [row for row in reader]
    images = read_images(Path("./inputs/calibracion.pdf"), True)
    out_dir = TemporaryDirectory()
    debug_dir = TemporaryDirectory()
    error_dir = TemporaryDirectory()
    images = [
        (
            i,
            Path("calibracion.pdf"),
            config,
            np.array(img),
            out_dir.name,
            debug_dir.name,
            error_dir.name,
            None,
            "",
        )
        for i, img in enumerate(images)
    ]
    for data, result in zip(images, results):
        with subtests.test(
            "DIAD test formreturn forms", name=f"calibracion.pdf ({data[0] + 1})"
        ):
            res = proc_img(data)
            assert result == res
