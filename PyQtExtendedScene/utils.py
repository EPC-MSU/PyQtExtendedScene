from typing import List, Tuple
from PyQt5.QtCore import QPointF


def get_left_top_pos(points: List[QPointF]) -> Tuple[float, float]:
    """
    :param points:
    :return:
    """

    left, top = None, None
    for point in points:
        x, y = point.x(), point.y()
        if left is None or left > x:
            left = x
        if top is None or top > y:
            top = y
    return left, top
