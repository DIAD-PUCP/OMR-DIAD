import cv2
import numpy as np
from cv2.typing import MatLike


def calculate_values(aoi_bw: MatLike, aoi_gray: MatLike, mask: MatLike) -> float:
    aoi_weight = (mask * aoi_bw) * (255 - aoi_gray) / 255
    return cv2.sumElems(aoi_weight)[0]


def detect_selected_answer(
    marks: MatLike, area: int, threshold: float
) -> tuple[MatLike, MatLike]:
    odds = np.round(marks / area, 3)
    selected = (odds > 1.75 * np.std(odds)) & (odds >= threshold)
    return odds, selected
