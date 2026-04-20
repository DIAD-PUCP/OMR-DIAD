import cv2
import numpy as np
from cv2.typing import MatLike

from form import Form


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
    config: Form, marks: list[MatLike], threshold: float = 1.0
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
            ans = odds >= threshold
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
    _, img = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
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
