from itertools import chain

import cv2
import numpy as np
from cv2.typing import MatLike
from PIL import Image

from form import Barcode, Form, ItemBlock, OutputFormat
from form_id import find_barcode_id, find_itemblock_id
from preprocessing import preprocess_image_barcodes, preprocess_image_timing_marks


def apply_brightness_contrast(
    input_img: MatLike, brightness: int, contrast: int
) -> MatLike:
    if brightness != 0:
        if brightness > 0:
            shadow = brightness
            highlight = 255
        else:
            shadow = 0
            highlight = 255 + brightness
        alpha_b = (highlight - shadow) / 255
        gamma_b = shadow

        buf = cv2.addWeighted(input_img, alpha_b, input_img, 0, gamma_b)
    else:
        buf = input_img.copy()

    if contrast != 0:
        f = 131 * (contrast + 127) / (127 * (131 - contrast))
        alpha_c = f
        gamma_c = 127 * (1 - f)

        buf = cv2.addWeighted(buf, alpha_c, buf, 0, gamma_c)

    return buf


def debug_img(
    config: Form, src_img: MatLike, values: list[MatLike], answers: list[MatLike]
) -> MatLike:
    k = 0
    for segment in config.segments:
        position = np.array(segment.position)
        for block in segment.item_blocks:
            start = position + np.array(block.position)
            size = np.array(block.item_size)
            for j in range(block.nrows):
                for i in range(block.nopts):
                    pos0 = start + np.array([i, j]) * size
                    pos1 = pos0 + size
                    src_img = cv2.rectangle(src_img, pos0, pos1, color=(255, 0, 0, 255))
                    src_img = cv2.putText(
                        src_img,
                        str(values[k][j][i]),
                        pos0,
                        cv2.FONT_HERSHEY_SIMPLEX,
                        fontScale=0.24,
                        color=(255, 0, 0, 255),
                        thickness=1,
                        lineType=cv2.LINE_AA,
                    )
                src_img = cv2.putText(
                    src_img,
                    answers[k][j],
                    (pos0[0] + round(size[0] * 1.1), pos0[1] + round(size[1] * 0.65)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    fontScale=0.5,
                    color=(0, 0, 255, 255),
                    thickness=1,
                    lineType=cv2.LINE_AA,
                )
            k = k + 1
    return src_img


def process_mcq_marks(
    config: Form, marks: list[MatLike]
) -> tuple[list[MatLike], list[MatLike]]:
    k = 0
    answers = []
    probabilities = []
    for segment in config.segments:
        for block in segment.item_blocks:
            size = np.array(block.item_size)
            bubble = np.array(block.bubble_size)
            area = np.zeros((size[1], size[0]), dtype=np.uint8)
            area = cv2.ellipse(
                area,
                (round(size[0] / 2), round(size[1] / 2)),
                (round(bubble[0] / 2), round(bubble[1] / 2)),
                0,
                0,
                360,
                255,
                -1,
            )
            area = cv2.countNonZero(area)
            odds = np.round(marks[k] / (area - marks[k] + 1), 1)
            ans = (odds > (np.max(odds, axis=1, keepdims=True) / 2)) & (
                odds >= config.threshold
            )
            ans = np.strings.multiply(
                np.array(block.bubble_labels), ans.astype(np.int8)
            )
            ans = (",".join(filter(lambda x: x != "", a)) for a in ans)
            ans = np.array([" " if a == "" else a for a in ans])
            probabilities.append(odds)
            answers.append(ans)
            k = k + 1
    return (answers, probabilities)


def read_bubbles(config: Form, src_img: MatLike) -> list[MatLike]:
    image = apply_brightness_contrast(src_img, config.brightness, config.contrast)
    blur = cv2.medianBlur(image, ksize=5)
    gray = cv2.cvtColor(blur, cv2.COLOR_RGB2GRAY)
    if config.luminance is None:
        _, img = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    else:
        _, img = cv2.threshold(gray, config.luminance, 255, cv2.THRESH_BINARY_INV)
    results = []
    for segment in config.segments:
        position = np.array(segment.position)
        for block in segment.item_blocks:
            counts = np.zeros(shape=(block.nrows, block.nopts), dtype=np.uint16)
            start = position + np.array(block.position)
            size = np.array(block.item_size)
            bubble = np.array(block.bubble_size)
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
            for j in range(block.nrows):
                for i in range(block.nopts):
                    pos0 = start + np.array([i, j]) * size
                    pos1 = pos0 + size
                    aoi = img[pos0[1] : pos1[1], pos0[0] : pos1[0]]
                    aoi = cv2.bitwise_and(aoi, aoi, mask=mask)
                    counts[j, i] = cv2.countNonZero(aoi)
            results.append(counts)
    return results


def process_form(
    config: Form, image: MatLike, output_dir: str = ".", debug_dir: str = "."
) -> list[str]:
    if isinstance(config.form_id, Barcode):
        res = preprocess_image_barcodes(config, image)
        formid = find_barcode_id(config, image)
    elif isinstance(config.form_id, ItemBlock):
        res = preprocess_image_timing_marks(config, image)
        formid = find_itemblock_id(config, res)
    marks = read_bubbles(config, res)
    ans, prob = process_mcq_marks(config, marks)
    Image.fromarray(res).save(f"{output_dir}/{formid}.png")
    debug = debug_img(config, res, prob, ans)
    Image.fromarray(debug).save(f"{debug_dir}/{formid}.png")
    return [str(formid)] + list(chain.from_iterable(ans))


def format_output(config: Form, results: list[list[str]], format: OutputFormat) -> str:
    res = []
    if format == OutputFormat.DAT:
        for ficha in results:
            line = []
            for i, el in enumerate(ficha):
                if i > 0 and len(el) > 1:
                    line.append("*")
                else:
                    line.append(el)
            res.append("".join(line))
        return "\n".join(sorted(res))
    else:
        for ficha in results:
            res.append(",".join([f'"{el}"' for el in ficha]))
        header = ",".join([f'"{col}"' for col in config.get_header()])
        return header + "\n" + "\n".join(sorted(res))
