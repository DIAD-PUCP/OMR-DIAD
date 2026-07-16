import csv
import sys
from io import BytesIO
from multiprocessing import Pool
from pathlib import Path
from typing import Annotated, Optional

import numpy as np
import pdf2image
import tqdm
import typer
from PIL import Image
from pypdf import PdfReader

from omr_diad.form import Form, OutputFormat
from omr_diad.generate import draw_form, generate_forms_html
from omr_diad.processing import format_output, process_form, read_source_data

app = typer.Typer()


@app.command()
def generate_template(
    config_file: Annotated[
        Path, typer.Option(dir_okay=False, readable=True, exists=True)
    ],
    decorations_file: Annotated[
        Path, typer.Option(dir_okay=False, readable=True, exists=True)
    ],
):
    with open(config_file) as f:
        json_config = f.read()
        config = Form.model_validate_json(json_config)
    with open(decorations_file) as f:
        decorations = f.read()
    form = draw_form(config, decorations)
    print(form)


@app.command()
def generate_forms(
    config_file: Annotated[
        Path, typer.Option(dir_okay=False, readable=True, exists=True)
    ],
    data_file: Annotated[
        Path, typer.Option(dir_okay=False, readable=True, exists=True)
    ],
    decorations_file: Annotated[
        Path, typer.Option(dir_okay=False, readable=True, exists=True)
    ],
    custom_elements_file: Annotated[
        Optional[Path], typer.Option(dir_okay=False, readable=True, exists=True)
    ] = None,
):
    with open(config_file) as f:
        json_config = f.read()
        config = Form.model_validate_json(json_config)
    with open(data_file) as f:
        data = [d for d in csv.DictReader(f)]
    with open(decorations_file) as f:
        decorations = f.read()
    if custom_elements_file is not None:
        with open(custom_elements_file) as f:
            custom = f.read()
    else:
        custom = ""
    forms = generate_forms_html(config, custom, data, decorations)
    print(forms)


def proc_img(data) -> Optional[list[str]]:
    i, fname, config, image, out, debug, error, source_data, data_key = data
    try:
        result = process_form(
            config,
            image,
            output_dir=out,
            debug_dir=debug,
            extra={
                "filename": fname,
                "page_num": i + 1,
                "data": source_data,
                "data_key": data_key,
            },
        )
        return result
    except RuntimeError as e:
        print(e, file=sys.stderr)
        Image.fromarray(image).save(f"{error}/({i + 1})_{fname.parts[-1]}")
        return None


def read_images(pdf_path: Path, convert_image: bool = False) -> list[Image.Image]:
    if not convert_image:
        reader = PdfReader(pdf_path)
        return [Image.open(BytesIO(page.images[0].data)) for page in reader.pages]
    else:
        return pdf2image.convert_from_path(pdf_path, fmt="jpeg")


@app.command()
def process(
    fnames: Annotated[list[Path], typer.Argument()],
    config_file: Annotated[
        Path, typer.Option(dir_okay=False, readable=True, exists=True)
    ],
    data_file: Annotated[
        Optional[Path], typer.Option(dir_okay=False, readable=True, exists=True)
    ] = None,
    data_id: Annotated[str, typer.Option()] = "form_id",
    data_key: Annotated[str, typer.Option()] = "EXAMEN",
    single_process: Annotated[bool, typer.Option()] = False,
    convert: Annotated[bool, typer.Option()] = False,
    out_dir: Annotated[
        Path, typer.Option(file_okay=False, exists=True, writable=True)
    ] = Path("outputs"),
    debug_dir: Annotated[
        Path, typer.Option(file_okay=False, exists=True, writable=True)
    ] = Path("debug"),
    error_dir: Annotated[
        Path, typer.Option(file_okay=False, exists=True, writable=True)
    ] = Path("errors"),
    output_format: Annotated[OutputFormat, typer.Option()] = OutputFormat.CSV,
):
    with open(config_file) as f:
        json_config = f.read()
        config = Form.model_validate_json(json_config)

    if data_file is not None:
        source_data = read_source_data(data_file, data_id)
    else:
        source_data = None

    for n, fname in enumerate(fnames):
        print(f"Processing {fname}:", file=sys.stderr)
        images = read_images(fname, convert)
        images = [
            (
                i,
                fname,
                config,
                np.array(img),
                out_dir,
                debug_dir,
                error_dir,
                source_data,
                data_key,
            )
            for i, img in enumerate(images)
        ]

        if not single_process:
            with Pool() as p:
                results = list(tqdm.tqdm(p.imap(proc_img, images), total=len(images)))
        else:
            results = []
            for data in tqdm.tqdm(images):
                results.append(proc_img(data))

        output = format_output(
            config, results, output_format, use_header=(n == 0), source_data=source_data
        )
        print(output)


if __name__ == "__main__":
    app()
