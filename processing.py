import cv2
import numpy as np
from cv2.typing import MatLike
from PIL import Image

from form import Form


def debug_img(config: Form, src_img: MatLike, values=list[MatLike]) -> MatLike:
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
            k = k + 1
    return src_img


def read_bubbles(config: Form, src_img: MatLike) -> list[MatLike]:
    blur = cv2.GaussianBlur(src_img, ksize=(3, 3), sigmaX=0)
    gray = cv2.cvtColor(blur, cv2.COLOR_RGB2GRAY)
    _, img = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    Image.fromarray(img).save("debug.png")
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
