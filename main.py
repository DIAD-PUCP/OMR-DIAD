import sys

import numpy as np
import pdf2image
import tqdm

from form import Form
from processing import process_form


def main(args):
    config_file = args[1]
    fname = args[2]
    with open(config_file) as f:
        json_config = f.read()
        config = Form.model_validate_json(json_config)

    images = [
        np.array(img)
        for img in pdf2image.convert_from_path(fname, fmt="jpeg", thread_count=8)
    ]
    results = []
    for image in tqdm.tqdm(images):
        try:
            result = process_form(
                config, image, output_dir="outputs", debug_dir="debug"
            )
            results.append(result)
        except RuntimeError as e:
            print(e)
            continue
    r = []
    for ficha in results:
        line = []
        for _, el in enumerate(ficha):
            line.append(f'"{el}"')
        r.append(",".join(line))
    print("\n".join(sorted(r)))


if __name__ == "__main__":
    main(sys.argv)
    exit(0)
