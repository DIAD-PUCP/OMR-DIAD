import cv2
import numpy as np
from cv2.typing import MatLike
from numpy.typing import NDArray


def calculate_values(aoi_bw: MatLike, aoi_gray: MatLike, mask: MatLike) -> float:
    aoi_weight = (mask * aoi_bw) * (255 - aoi_gray) / 255
    return cv2.sumElems(aoi_weight)[0]


def detect_selected_answer(
    marks: MatLike, area: int, threshold: float
) -> tuple[MatLike, NDArray, NDArray]:
    odds = marks / area
    ppf = 1.9599 * np.std(odds, axis=1, keepdims=True)
    thr_ratio = odds / threshold
    odd_ratio = odds / ppf
    selected = (odds >= ppf) & (odds >= threshold)
    return np.round(odds, 3), selected, np.round(np.minimum(thr_ratio, odd_ratio), 3)
