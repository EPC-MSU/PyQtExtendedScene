import sys
import time
from typing import List, Optional
from PyQt5.QtCore import QPointF, Qt
from PyQt5.QtGui import QPen


def get_class_by_name(class_name: str) -> Optional[type]:
    """
    :param class_name: class name.
    :return: class with the given name.
    """

    for module in sys.modules.values():
        if hasattr(module, class_name):
            return getattr(module, class_name)

    return None


def get_dashed_pen(solid_pen: QPen) -> QPen:
    """
    :param solid_pen: solid pen.
    :return: dashed pen.
    """

    pen = QPen(solid_pen)
    pen.setStyle(Qt.CustomDashLine)
    pattern = 0, 3, 0, 3, 3, 0, 3, 0
    update_interval = 0.4
    mod = int(time.monotonic() / update_interval) % (len(pattern) // 2)
    pen.setDashPattern(pattern[mod * 2:] + pattern[:mod * 2])
    return pen


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
