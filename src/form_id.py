import cv2
import numpy as np
import zxingcpp
from cv2.typing import MatLike

from form import Barcode, BarcodesSegment, Form, ItemBlock


def find_barcode_id(config: Form, src_img: MatLike) -> str:
    code = config.form_id
    if not isinstance(code, Barcode):
        raise RuntimeError("Config file does not define a barcode_id")
    segment_barcodes = []
    for segment in config.segments:
        if isinstance(segment, BarcodesSegment):
            segment_barcodes.append(segment.bottom_left.text)
            segment_barcodes.append(segment.top_right.text)

    barcodes = zxingcpp.read_barcodes(
        src_img, try_rotate=False, formats=[zxingcpp.BarcodeFormat.Code128]
    )

    for bcode in barcodes:
        if bcode.text not in segment_barcodes:
            return bcode.text.split("-")[0]
    raise RuntimeError("Form ID barcode not found")


def find_itemblock_id(config: Form, src_img: MatLike) -> str:
    id_block = config.form_id
    if not isinstance(id_block, ItemBlock):
        raise RuntimeError("Config file does not define a ItemBlock Id")
    size = np.array(id_block.item_size)
    pos = np.array(id_block.position)
    nrows = id_block.nrows
    nopts = id_block.nopts
    bubble = np.array(id_block.bubble_size)
    counts = np.zeros(shape=(nrows, nopts), dtype=np.uint16)
    mask = np.zeros((size[1], size[0]), dtype=np.uint8)
    mask = cv2.ellipse(
        mask,
        (round(size[0] / 2), round(size[1] / 2)),
        (round(bubble[0] / 2), round(bubble[1] / 2)),
        0,
        0,
        360,
        255,
        -1,
    )
    block = src_img[
        pos[1] : pos[1] + (size[1] * nrows), pos[0] : pos[0] + (size[0] * nopts)
    ]
    blur = cv2.GaussianBlur(block, ksize=(3, 3), sigmaX=0)
    gray = cv2.cvtColor(blur, cv2.COLOR_RGB2GRAY)
    _, img = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    for j in range(nrows):
        for i in range(nopts):
            pos0 = np.array([i, j]) * size
            pos1 = pos0 + size
            aoi = img[pos0[1] : pos1[1], pos0[0] : pos1[0]]
            aoi = cv2.bitwise_and(aoi, aoi, mask=mask)
            counts[j, i] = cv2.countNonZero(aoi)
    ans = counts >= 120
    res = np.sum(
        ans.reshape(counts.shape[1], counts.shape[0]).astype(np.int8)
        * np.array([2**i for i in range(30)])
    )
    return str(res)
