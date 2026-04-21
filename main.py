import os
import sys
from multiprocessing import Pool
from pathlib import Path
from typing import Annotated, Optional

import numpy as np
import pdf2image
import tqdm
import typer
from PIL import Image

from form import Form, OutputFormat
from processing import format_output, process_form

app = typer.Typer()


def proc_img(data) -> Optional[list[str]]:
    i, fname, config, image, out, debug, error = data
    try:
        result = process_form(config, image, output_dir=out, debug_dir=debug)
        return result
    except RuntimeError as e:
        print(e, file=sys.stderr)
        Image.fromarray(image).save(f"{error}/({i + 1})_{fname}")
        return None


@app.command()
def main(
    fname: Annotated[Path, typer.Argument()],
    config_file: Annotated[
        Path, typer.Option(dir_okay=False, readable=True, exists=True)
    ],
    single_process: Annotated[bool, typer.Option()] = False,
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
    n_threads = os.cpu_count() or 1
    images = [
        (i, fname, config, np.array(img), out_dir, debug_dir, error_dir)
        for i, img in enumerate(
            pdf2image.convert_from_path(fname, fmt="jpeg", thread_count=n_threads)
        )
    ]

    if not single_process:
        with Pool() as p:
            results = list(tqdm.tqdm(p.imap(proc_img, images), total=len(images)))
    else:
        results = []
        for data in tqdm.tqdm(images):
            results.append(proc_img(data))

    output = format_output(config, results, output_format)
    print(output)


if __name__ == "__main__":
    app()
