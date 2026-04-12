import sys

import numpy as np
import pdf2image
import tqdm
from PIL import Image

from form import Form
from form_id import find_barcode_id
from preprocessing import preprocess_image_barcodes


def main(args):
    config_file = args[1]
    fname = args[2]
    with open(config_file) as f:
        json_config = f.read()
        config = Form.model_validate_json(json_config)

    images = pdf2image.convert_from_path(fname)
    for i, img in enumerate(tqdm.tqdm(images)):
        image = np.array(img)
        res = preprocess_image_barcodes(config, image, deskew="barcodes")
        formid = find_barcode_id(config, image)
        Image.fromarray(res).save(f"{formid}({i}).png")


if __name__ == "__main__":
    main(sys.argv)
    exit(0)
