import cv2
import numpy as np
import zxingcpp
from cv2.typing import MatLike

from form import BarcodesSegment, Form


def find_skew(
    src_img: MatLike, bottom_left: zxingcpp.Barcode, top_right: zxingcpp.Barcode
) -> float:
    return 0


def preprocess_image_barcodes(config: Form, src_img: MatLike) -> MatLike:
    for s in config.segments:
        if isinstance(s, BarcodesSegment):
            segment = s
            break
    else:
        raise RuntimeError("No barcode segments in config")

    bottom_left = None
    top_right = None

    blur_img = cv2.GaussianBlur(src_img, ksize=(3, 3), sigmaX=0)
    barcodes = zxingcpp.read_barcodes(
        blur_img, try_rotate=False, formats=[zxingcpp.BarcodeFormat.Code128]
    )
    for code in barcodes:
        if code.text == segment.bottom_left.text:
            bottom_left = code
        elif code.text == segment.top_right.text:
            top_right = code
        else:
            continue

    if (bottom_left is None) or (top_right is None):
        raise RuntimeError("Segment barcodes not found")

    skew = find_skew(blur_img, bottom_left, top_right)
    rot_mat = cv2.getRotationMatrix2D((0, 0), -skew, 1)

    img = cv2.warpAffine(
        src_img,
        rot_mat,
        (src_img.shape[1], src_img.shape[0]),
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=0,
        flags=cv2.INTER_LANCZOS4,
    )

    blur_img = cv2.GaussianBlur(img, ksize=(3, 3), sigmaX=0)
    barcodes = zxingcpp.read_barcodes(blur_img)
    for code in barcodes:
        if code.text == segment.bottom_left.text:
            bottom_left = code
        elif code.text == segment.top_right.text:
            top_right = code
        else:
            continue

    if (bottom_left is None) or (top_right is None):
        raise RuntimeError("Segment barcodes not found")

    bl = bottom_left.position.bottom_left
    tr = top_right.position.top_right

    segment_width = tr.x - bl.x
    segment_height = bl.y - tr.y
    scale_factor = np.array(segment.size) / np.array([segment_width, segment_height])
    position = np.array([bl.x, tr.y])
    offset = np.array(segment.position) - (position * scale_factor)
    img = cv2.resize(
        img,
        None,
        fx=scale_factor[0],
        fy=scale_factor[1],
        interpolation=cv2.INTER_LINEAR,
    )

    tmat = np.array([[1, 0, offset[0]], [0, 1, offset[1]]], dtype=np.float32)
    img = cv2.warpAffine(
        img,
        tmat,
        dsize=(img.shape[1], img.shape[0]),
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=(255, 255, 255, 255),
    )

    img = cv2.copyMakeBorder(
        img, 0, 50, 0, 50, cv2.BORDER_CONSTANT, value=(255, 255, 255, 255)
    )
    img = img[0 : config.page_size[1], 0 : config.page_size[0]]

    return img
