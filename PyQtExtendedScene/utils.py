from typing import List
from PyQt5.QtCore import QPointF


def get_left_top_pos(points: List[QPointF]) -> QPointF:
    """
    :param points: list of points.
    :return: point with the smallest coordinate of points along the x and y axes.
    """

    left, top = None, None
    for point in points:
        x, y = point.x(), point.y()
        if left is None or left > x:
            left = x
        if top is None or top > y:
            top = y
    return QPointF(left, top)
