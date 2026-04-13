import sys

import numpy as np
import pdf2image
import tqdm
from PIL import Image

from form import Form
from form_id import find_barcode_id
from preprocessing import preprocess_image_barcodes
from processing import debug_img, process_mcq_marks, read_bubbles


def main(args):
    config_file = args[1]
    fname = args[2]
    with open(config_file) as f:
        json_config = f.read()
        config = Form.model_validate_json(json_config)

    images = pdf2image.convert_from_path(fname)
    for i, img in enumerate(tqdm.tqdm(images)):
        try:
            image = np.array(img)
            res = preprocess_image_barcodes(config, image, deskew="barcodes")
            formid = find_barcode_id(config, image)
            marks = read_bubbles(config, res)
            ans, prob = process_mcq_marks(config, marks)
            Image.fromarray(res).save(f"outputs/{formid}({i}).png")
            debug = debug_img(config, res, prob, ans)
            Image.fromarray(debug).save(f"debug/{formid}({i}).png")
        except RuntimeError as e:
            print(e)
            Image.fromarray(image).save(f"errors/{fname.split('/')[-1]}({i}).png")
            continue


if __name__ == "__main__":
    main(sys.argv)
    exit(0)
