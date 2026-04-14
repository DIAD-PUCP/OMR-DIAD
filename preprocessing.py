import cv2
import numpy as np
import zxingcpp
from cv2.typing import MatLike
from numpy.typing import NDArray

from form import BarcodesSegment, Form, TimingMarksSegment


def find_skew(src_img: MatLike) -> tuple[float, float, float]:
    gray = cv2.cvtColor(src_img, cv2.COLOR_RGB2GRAY)
    _, img_bin = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    lines = cv2.HoughLinesP(
        img_bin,
        1,
        np.pi / 360,
        50,
        minLineLength=src_img.shape[0] / 4,
        maxLineGap=10,
    )
    angles = []
    xs = []
    ys = []
    for line in lines:
        x1, y1, x2, y2 = line[0]
        xs.append(x1)
        ys.append(y1)
        angles.append(np.atan2(y2 - y1, x2 - x1))
        cv2.line(src_img, (x1, y1), (x2, y2), (0, 255, 0), 1)
    skew = np.median(angles)
    x = np.median(xs)
    y = np.median(ys)
    return skew * 180 / np.pi, x, y


def find_skew_barcode(
    src_img: MatLike, code: zxingcpp.Barcode
) -> tuple[float, float, float]:
    width = code.position.top_right.x - code.position.bottom_left.x
    pad = int(width / 20)
    code_img = src_img[
        code.position.top_left.y - pad : code.position.bottom_right.y + pad,
        code.position.top_left.x - pad : code.position.bottom_right.x + pad,
    ]
    code_gray = cv2.cvtColor(code_img, cv2.COLOR_RGB2GRAY)
    _, code_bin = cv2.threshold(
        code_gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
    )
    contours, _ = cv2.findContours(code_bin, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    first_x = code_bin.shape[1]
    last_x = 0
    first, last = None, None
    for c in contours:
        rot_box = cv2.minAreaRect(c)
        if rot_box[0][0] < first_x:
            first_x = rot_box[0][0]
            first = rot_box
        if rot_box[0][0] > last_x:
            last_x = rot_box[0][0]
            last = rot_box
    if not first or not last:
        raise RuntimeError("Could not detect barcode skew")

    first = np.array(first[0])
    last = np.array(last[0])
    vec = last - first
    angle = np.atan2(vec[1], vec[0]) * 180 / np.pi
    return (angle, first[0], last[0])


def find_timing_marks(
    timing_area: MatLike,
    marker_area_limits: tuple[float, float],
    aspect_ratio_limits: tuple[float, float],
    is_skewed: bool = True,
) -> NDArray:
    min_area, max_area = marker_area_limits
    min_ar, max_ar = aspect_ratio_limits
    inv_min_ar = 1 / max_ar
    inv_max_ar = 1 / min_ar
    gray = cv2.cvtColor(timing_area, cv2.COLOR_RGB2GRAY)
    _, img_bin = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    contours, _ = cv2.findContours(img_bin, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    rects = []
    for c in contours:
        area = cv2.contourArea(c, oriented=True)
        if min_area < area < max_area:
            if is_skewed:
                r = cv2.minAreaRect(c)
                rect = np.array([r[0][0], r[0][1], r[1][0], r[1][1]])
            else:
                rect = np.array(cv2.boundingRect(c))
            ar = rect[2] / rect[3]
            if (min_ar < ar < max_ar) or (inv_min_ar < ar < inv_max_ar):
                rects.append(rect)
    return np.sort(rects, axis=0)


def find_skew_timing_marks(timing_marks: NDArray) -> tuple[float, float, float]:
    first = timing_marks[0]
    last = timing_marks[-1]
    vec = last[:2] - first[:2]
    angle = np.atan2(vec[1], vec[0]) * 180 / np.pi
    return (-angle, first[0], first[1])


def find_segment_top(src_img: MatLike) -> float:
    # We calculate the height using the frame of the litho
    top = round(src_img.shape[0] * 0.1)
    img = src_img[:top, :]
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    _, img_bin = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    nonzero = np.nonzero(img_bin[:top, :])
    top_start = np.min(nonzero[0])
    left_start = np.min(nonzero[1])
    # skip 1% of top and keep 20% middle to ignore borders
    pad = np.ceil(np.array(src_img.shape[:-1]) * np.array([0.01, 0.75])).astype(
        np.int64
    )
    image_top = img_bin[
        top_start + pad[0] : top,
        left_start + round(pad[1] / 2) : img_bin.shape[1] - round(pad[1] / 2),
    ]
    extra_pad = np.argmax(np.mean(image_top.astype(float), axis=1) >= 254)
    y1 = (
        top_start
        + pad[0]
        + extra_pad
        + np.argmax(np.mean(image_top[extra_pad:, :].astype(float), axis=1) < 250)
    )  # first slightly black line
    return y1


def find_segment_barcodes(
    img: MatLike, segment: BarcodesSegment
) -> tuple[zxingcpp.Barcode, zxingcpp.Barcode]:
    barcodes = zxingcpp.read_barcodes(
        img, try_rotate=False, formats=[zxingcpp.BarcodeFormat.Code128]
    )
    bottom_left = None
    top_right = None
    for code in barcodes:
        if code.text == segment.bottom_left.text:
            bottom_left = code
        elif code.text == segment.top_right.text:
            top_right = code
        else:
            continue

    if (bottom_left is None) or (top_right is None):
        raise RuntimeError("Segment barcodes not found")
    return (bottom_left, top_right)


def preprocess_image_barcodes(
    config: Form, src_img: MatLike, deskew: str = "lines"
) -> MatLike:
    for s in config.segments:
        if isinstance(s, BarcodesSegment):
            segment = s
            break
    else:
        raise RuntimeError("No barcode segments in config")

    blur_img = cv2.GaussianBlur(src_img, ksize=(3, 3), sigmaX=0)

    if deskew == "lines":
        skew, x, y = find_skew(blur_img)
    else:
        bottom_left, top_right = find_segment_barcodes(blur_img, segment)
        skew1, x, y = find_skew_barcode(blur_img, bottom_left)
        skew2, _, _ = find_skew_barcode(blur_img, top_right)
        skew = (skew1 + skew2) / 2

    rot_mat = cv2.getRotationMatrix2D((x, y), skew, 1)

    img = cv2.warpAffine(
        src_img,
        rot_mat,
        (src_img.shape[1], src_img.shape[0]),
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=0,
        flags=cv2.INTER_LANCZOS4,
    )

    blur_img = cv2.GaussianBlur(img, ksize=(3, 3), sigmaX=0)
    bottom_left, top_right = find_segment_barcodes(blur_img, segment)

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


def preprocess_image_timing_marks(
    config: Form, src_img: MatLike, deskew: str = "lines"
) -> MatLike:
    for s in config.segments:
        if isinstance(s, TimingMarksSegment):
            segment = s
            break
    else:
        raise RuntimeError("No Timing Marks segments in config")

    blur_img = cv2.GaussianBlur(src_img, ksize=(3, 3), sigmaX=0)
    # Must implement a more robust timing area detection
    # Now it asumes is the bottom 10% of image
    timing_start = round(src_img.shape[0] * 0.90)
    timing_area = blur_img[timing_start:, :]
    img_area = src_img.shape[0] * src_img.shape[1]
    marker_area_limits = (img_area * 15 / 100_000, img_area * 30 / 100_000)
    aspect_ratio_limits = (0.3, 0.6)
    # Must implement a more robust timing mark detection,
    # now it calculates black boxes within some area and aspect ratio limits
    timing_marks = find_timing_marks(
        timing_area, marker_area_limits, aspect_ratio_limits
    )

    if deskew == "lines":
        skew, x, y = find_skew(blur_img)
    else:
        skew, x, y = find_skew_timing_marks(timing_marks)

    rot_mat = cv2.getRotationMatrix2D((x, y + timing_start), skew, 1)

    img = cv2.warpAffine(
        src_img,
        rot_mat,
        (src_img.shape[1], src_img.shape[0]),
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=0,
        flags=cv2.INTER_LANCZOS4,
    )

    # Timing marks are recalculated on rotated image
    blur_img = cv2.GaussianBlur(img, ksize=(3, 3), sigmaX=0)
    timing_start = round(img.shape[0] * 0.90)
    timing_area = blur_img[timing_start:, :]
    timing_marks = find_timing_marks(
        timing_area, marker_area_limits, aspect_ratio_limits, is_skewed=False
    )
    start_x = np.min(timing_marks[:, 0])
    median_y = np.median(timing_marks[:, 1])
    median_width = np.median(timing_marks[:, 2])
    median_height = np.median(timing_marks[:, 3])
    segment_width = timing_marks[-1][0] - timing_marks[0][0] + median_width
    end_y = round(timing_start + median_y + median_height)
    start_y = find_segment_top(blur_img)
    segment_height = end_y - start_y

    scale_factor = np.array(segment.size) / np.array([segment_width, segment_height])
    position = np.array([start_x, start_y])
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
