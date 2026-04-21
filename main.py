import os
import sys
from multiprocessing import Pool
from typing import Annotated, Optional

import numpy as np
import pdf2image
import tqdm
import typer

from form import Form
from processing import process_form

app = typer.Typer()


def proc_img(data) -> Optional[list[str]]:
    config, image, out, debug = data
    try:
        result = process_form(config, image, output_dir=out, debug_dir=debug)
        return result
    except RuntimeError as e:
        print(e, file=sys.stderr)
        return None


@app.command()
def main(
    config_file: Annotated[str, typer.Argument()],
    fname: Annotated[str, typer.Argument()],
    single_process: Annotated[bool, typer.Option()] = False,
):
    with open(config_file) as f:
        json_config = f.read()
        config = Form.model_validate_json(json_config)
    n_threads = os.cpu_count() or 1
    images = [
        (config, np.array(img), "outputs", "debug")
        for img in pdf2image.convert_from_path(
            fname, fmt="jpeg", thread_count=n_threads
        )
    ]

    if not single_process:
        with Pool() as p:
            results = list(tqdm.tqdm(p.imap(proc_img, images), total=len(images)))
    else:
        results = []
        for data in tqdm.tqdm(images):
            results.append(proc_img(data))

    r = []
    for ficha in results:
        if ficha is None:
            continue
        line = []
        for _, el in enumerate(ficha):
            line.append(f'"{el}"')
        r.append(",".join(line))
    print("\n".join(sorted(r)))


if __name__ == "__main__":
    app()
