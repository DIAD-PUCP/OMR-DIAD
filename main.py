import sys

import numpy as np
import pdf2image
import tqdm
from PIL import Image

from form import Form
from preprocessing import preprocess_image_barcodes


def main(args):
    config_file = args[1]
    fname = args[2]
    with open(config_file) as f:
        json_config = f.read()
        config = Form.model_validate_json(json_config)

    images = pdf2image.convert_from_path(fname)
    for i, img in enumerate(tqdm.tqdm(images)):
        res = preprocess_image_barcodes(config, np.array(img), deskew="barcodes")
        Image.fromarray(res).save(f"{i}.png")


if __name__ == "__main__":
    main(sys.argv)
    exit(0)
