import sys
from itertools import chain

import numpy as np
import pdf2image
import tqdm
from PIL import Image

from form import Barcode, Form, ItemBlock
from form_id import find_barcode_id, find_itemblock_id
from preprocessing import preprocess_image_barcodes, preprocess_image_timing_marks
from processing import debug_img, process_mcq_marks, read_bubbles


def main(args):
    config_file = args[1]
    fname = args[2]
    with open(config_file) as f:
        json_config = f.read()
        config = Form.model_validate_json(json_config)

    images = pdf2image.convert_from_path(fname, fmt="jpeg", thread_count=8)
    results = []
    for i, img in enumerate(tqdm.tqdm(images)):
        try:
            image = np.array(img)
            if isinstance(config.form_id, Barcode):
                res = preprocess_image_barcodes(config, image)
                formid = find_barcode_id(config, image)
            elif isinstance(config.form_id, ItemBlock):
                res = preprocess_image_timing_marks(config, image)
                formid = find_itemblock_id(config, res)
            else:
                raise RuntimeError("Form ID not valid")
            marks = read_bubbles(config, res)
            ans, prob = process_mcq_marks(config, marks)
            Image.fromarray(res).save(f"outputs/{formid}({i}).png")
            debug = debug_img(config, res, prob, ans)
            Image.fromarray(debug).save(f"debug/{formid}({i}).png")
            results.append([str(formid)] + list(chain.from_iterable(ans)))
        except RuntimeError as e:
            print(e)
            Image.fromarray(image).save(f"errors/{fname.split('/')[-1]}({i}).png")
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
