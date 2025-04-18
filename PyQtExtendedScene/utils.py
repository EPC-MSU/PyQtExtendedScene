import math
import sys
import time
from typing import Any, Callable, List, Optional
from PyQt5.QtCore import QPoint, QPointF, QRectF, QSizeF, Qt
from PyQt5.QtGui import QBrush, QColor, QPen
from PyQt5.QtWidgets import QGraphicsView


MIN_DIMENSION: float = 64


def create_pen(color: QColor, width: float) -> QPen:
    """
    :param color: pen color;
    :param width: pen width.
    :return: default pen for component.
    """

    pen = QPen(QBrush(color), width)
    return pen


def fit_rect_to_background(background_rect: QRectF, rect: QRectF) -> Optional[QRectF]:
    """
    :param background_rect: background bounding rectangle;
    :param rect: rectangle.
    :return: a rectangle that lies inside the background.
    """

    if (background_rect.right() < rect.left() or rect.right() < background_rect.left() or
            background_rect.bottom() < rect.top() or rect.bottom() < background_rect.top()):
        return None

    return rect.intersected(background_rect)


def get_class_by_name(class_name: str) -> Optional[type]:
    """
    :param class_name: class name.
    :return: class with the given name.
    """

    for module in sys.modules.values():
        if hasattr(module, class_name):
            return getattr(module, class_name)

    return None


def get_function_to_update_dashed_pen(pen: QPen, update_interval: float = 0.4) -> Callable[[], QPen]:
    """
    :param pen: pen;
    :param update_interval: update interval.
    :return: function that returns dashed pen.
    """

    def get_dashed_pen() -> QPen:
        """
        :return: dashed pen.
        """

        new_pen = QPen(pen)
        new_pen.setStyle(Qt.CustomDashLine)
        pattern = 0, 3, 0, 3, 3, 0, 3, 0
        mod = int(time.monotonic() / update_interval) % (len(pattern) // 2)
        new_pen.setDashPattern(pattern[mod * 2:] + pattern[:mod * 2])
        return new_pen

    return get_dashed_pen


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


def get_max_zoom_factor(view: QGraphicsView) -> float:
    """
    :param view: view.
    :return: maximum magnification factor.
    """

    disp_height = map_length_to_scene(view, view.viewport().height())
    disp_width = map_length_to_scene(view, view.viewport().width())
    return min(disp_height, disp_width) / MIN_DIMENSION


def get_min_zoom_factor(view: QGraphicsView, image_size: QSizeF) -> float:
    """
    :param view: view;
    :param image_size: background image size.
    :return: minimum magnification factor.
    """

    image_height = image_size.height()
    image_width = image_size.width()
    disp_height = map_length_to_scene(view, view.viewport().height())
    disp_width = map_length_to_scene(view, view.viewport().width())
    if disp_height > 0 and disp_width > 0 and image_height > 0 and image_width > 0:
        return min(disp_height / image_height, disp_width / image_width)

    return 1.0


def map_length_to_scene(view: QGraphicsView, length: float) -> float:
    """
    :param view: view whose scene you need to relate the length to;
    :param length: length.
    :return: length on scene.
    """

    point_1, point_2 = QPoint(0, 0), QPoint(0, length)
    scene_point1, scene_point2 = view.mapToScene(point_1), view.mapToScene(point_2)
    return math.sqrt((scene_point2.x() - scene_point1.x()) ** 2 + (scene_point2.y() - scene_point1.y()) ** 2)


def send_edited_components_changed_signal(func):
    """
    A decorator that sends a signal that the edited components have changed.
    :param func: decorated function.
    """

    def wrapper(self, *args, **kwargs) -> Any:
        result = func(self, *args, **kwargs)
        self.edited_components_changed.emit()
        return result

    return wrapper
