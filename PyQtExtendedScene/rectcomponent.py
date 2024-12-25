from enum import auto, Enum
from typing import Any, Callable, Dict, Optional, Tuple, Union
from PyQt5.QtCore import QPointF, QRectF, Qt
from PyQt5.QtGui import QBrush, QColor, QPainter, QPen
from PyQt5.QtWidgets import (QGraphicsItem, QGraphicsRectItem, QGraphicsSceneHoverEvent, QStyle,
                             QStyleOptionGraphicsItem, QWidget)
from . import utils as ut
from .basecomponent import BaseComponent
from .pointcomponent import PointComponent
from .scenemode import SceneMode


def change_rect_and_pos(func: Callable[[QPointF], Tuple[float, float]]):
    """
    Decorator changes the position and size of the rectangular component.
    :param func: decorated function.
    """

    def wrapper(self, pos: QPointF) -> None:
        """
        :param pos: mouse position.
        """

        width, height = func(self, pos)
        self.setRect(0, 0, width, height)
        x = self.pos().x() if self._x_fixed is None else min(pos.x(), self._x_fixed)
        y = self.pos().y() if self._y_fixed is None else min(pos.y(), self._y_fixed)
        self.setPos(x, y)

    return wrapper


class RectComponent(QGraphicsRectItem, BaseComponent):
    """
    Rectangular component that can be drawn with the mouse and resized.
    """

    class Mode(Enum):
        """
        Enumerates the modes in which the component can be.
        """

        MOVE = auto()  # moving a component
        NO_ACTION = auto()
        RESIZE_ANY = auto()
        RESIZE_BOTTOM = auto()  # resizing by moving the bottom side
        RESIZE_LEFT = auto()  # resizing by moving the left side
        RESIZE_LEFT_BOTTOM = auto()
        RESIZE_LEFT_TOP = auto()
        RESIZE_RIGHT = auto()  # resizing by moving the right side
        RESIZE_RIGHT_BOTTOM = auto()
        RESIZE_RIGHT_TOP = auto()
        RESIZE_TOP = auto()  # resizing by moving the top side

    class MousePosition(Enum):
        """
        Enumerating mouse positions on a component's boundary.
        """

        X_LEFT = auto()
        X_MIDDLE = auto()
        X_NEAR_LEFT = auto()
        X_NEAR_RIGHT = auto()
        X_RIGHT = auto()
        Y_BOTTOM = auto()
        Y_MIDDLE = auto()
        Y_NEAR_BOTTOM = auto()
        Y_NEAR_TOP = auto()
        Y_TOP = auto()

    BORDER_REGION: float = 3
    CURSORS = {Mode.MOVE: Qt.SizeAllCursor,
               Mode.NO_ACTION: Qt.ArrowCursor,
               Mode.RESIZE_BOTTOM: Qt.SizeVerCursor,
               Mode.RESIZE_LEFT: Qt.SizeHorCursor,
               Mode.RESIZE_LEFT_BOTTOM: Qt.SizeBDiagCursor,
               Mode.RESIZE_LEFT_TOP: Qt.SizeFDiagCursor,
               Mode.RESIZE_RIGHT: Qt.SizeHorCursor,
               Mode.RESIZE_RIGHT_BOTTOM: Qt.SizeFDiagCursor,
               Mode.RESIZE_RIGHT_TOP: Qt.SizeBDiagCursor,
               Mode.RESIZE_TOP: Qt.SizeVerCursor}
    DIAGONAL_PORTION: float = 0.05
    MIN_SIZE: float = 2
    PEN_COLOR: QColor = QColor("#0047AB")
    PEN_WIDTH: float = 2
    Z_VALUE: float = 1

    def __init__(self, rect: Optional[QRectF] = None, pen: Optional[QPen] = None,
                 update_pen_for_selection: Optional[Callable[[], QPen]] = None, draggable: bool = True,
                 selectable: bool = True, unique_selection: bool = False) -> None:
        """
        :param rect: rect for component;
        :param pen: common pen;
        :param update_pen_for_selection: a function that returns a pen to paint a component when the component is
        selected;
        :param draggable: True if component can be dragged;
        :param selectable: True if component can be selected;
        :param unique_selection: True if selecting this component should reset all others selections
        ('selectable' must be set).
        """

        QGraphicsRectItem.__init__(self)
        BaseComponent.__init__(self, draggable, selectable, unique_selection)

        self._mode: RectComponent.Mode = RectComponent.Mode.NO_ACTION
        self._pen: QPen = pen or ut.create_cosmetic_pen(self.PEN_COLOR, self.PEN_WIDTH)
        self._update_pen_for_selection: Optional[Callable[[], QPen]] = (update_pen_for_selection or
                                                                        ut.get_function_to_update_dashed_pen(self._pen))
        self._x_fixed: Optional[float] = None
        self._y_fixed: Optional[float] = None

        self.setPen(self._pen)
        self.setZValue(self.Z_VALUE)
        if rect is not None:
            self.setRect(rect)

    @classmethod
    def create_from_json(cls, data: Dict[str, Any]) -> "RectComponent":
        """
        :param data: a dictionary with basic attributes that can be used to create an object.
        :return: class instance.
        """

        pen = ut.create_cosmetic_pen(QColor(data["pen_color"]), data["pen_width"])
        component = RectComponent(QRectF(*data["rect"]), pen, None, data["draggable"],
                                  data["selectable"], data["unique_selection"])
        component.setBrush(QBrush(QColor(data["brush_color"]), data["brush_style"]))
        return component

    def _determine_mode(self, pos: QPointF) -> Mode:
        """
        :param pos: mouse position.
        :return: mode.
        """

        if self.isSelected() and self._scene_mode is not SceneMode.NORMAL and not self.is_in_group():
            return self._get_mode_by_mouse_position(pos)

        return RectComponent.Mode.NO_ACTION

    def _get_mode_by_mouse_position(self, pos: QPointF) -> Mode:
        """
        :param pos: mouse position.
        :return: mode.
        """

        x, y = pos.x(), pos.y()
        border_width = self.BORDER_REGION / self._scale_factor
        rect = self.rect()
        left = rect.x()
        width = rect.width()
        right = rect.right()
        top = rect.y()
        height = rect.height()
        bottom = rect.bottom()

        x_pos = None
        if left - border_width <= x <= left:
            x_pos = RectComponent.MousePosition.X_LEFT
        elif left <= x <= left + self.DIAGONAL_PORTION * width:
            x_pos = RectComponent.MousePosition.X_NEAR_LEFT
        elif left + self.DIAGONAL_PORTION * width < x < right - self.DIAGONAL_PORTION * width:
            x_pos = RectComponent.MousePosition.X_MIDDLE
        elif right <= x <= right + border_width:
            x_pos = RectComponent.MousePosition.X_RIGHT
        elif right - self.DIAGONAL_PORTION * width <= x <= right:
            x_pos = RectComponent.MousePosition.X_NEAR_RIGHT

        y_pos = None
        if top - border_width <= y <= top:
            y_pos = RectComponent.MousePosition.Y_TOP
        elif top <= y <= top + self.DIAGONAL_PORTION * height:
            y_pos = RectComponent.MousePosition.Y_NEAR_TOP
        elif top + self.DIAGONAL_PORTION * height < y < bottom - self.DIAGONAL_PORTION * height:
            y_pos = RectComponent.MousePosition.Y_MIDDLE
        elif bottom <= y <= bottom + border_width:
            y_pos = RectComponent.MousePosition.Y_BOTTOM
        elif bottom - self.DIAGONAL_PORTION * height <= y <= bottom:
            y_pos = RectComponent.MousePosition.Y_NEAR_BOTTOM

        return {(RectComponent.MousePosition.X_LEFT, RectComponent.MousePosition.Y_NEAR_TOP):
                RectComponent.Mode.RESIZE_LEFT_TOP,
                (RectComponent.MousePosition.X_LEFT, RectComponent.MousePosition.Y_TOP):
                RectComponent.Mode.RESIZE_LEFT_TOP,
                (RectComponent.MousePosition.X_NEAR_LEFT, RectComponent.MousePosition.Y_TOP):
                RectComponent.Mode.RESIZE_LEFT_TOP,
                (RectComponent.MousePosition.X_MIDDLE, RectComponent.MousePosition.Y_TOP):
                RectComponent.Mode.RESIZE_TOP,
                (RectComponent.MousePosition.X_RIGHT, RectComponent.MousePosition.Y_NEAR_TOP):
                RectComponent.Mode.RESIZE_RIGHT_TOP,
                (RectComponent.MousePosition.X_RIGHT, RectComponent.MousePosition.Y_TOP):
                RectComponent.Mode.RESIZE_RIGHT_TOP,
                (RectComponent.MousePosition.X_NEAR_RIGHT, RectComponent.MousePosition.Y_TOP):
                RectComponent.Mode.RESIZE_RIGHT_TOP,
                (RectComponent.MousePosition.X_RIGHT, RectComponent.MousePosition.Y_MIDDLE):
                RectComponent.Mode.RESIZE_RIGHT,
                (RectComponent.MousePosition.X_RIGHT, RectComponent.MousePosition.Y_NEAR_BOTTOM):
                RectComponent.Mode.RESIZE_RIGHT_BOTTOM,
                (RectComponent.MousePosition.X_RIGHT, RectComponent.MousePosition.Y_BOTTOM):
                RectComponent.Mode.RESIZE_RIGHT_BOTTOM,
                (RectComponent.MousePosition.X_NEAR_RIGHT, RectComponent.MousePosition.Y_BOTTOM):
                RectComponent.Mode.RESIZE_RIGHT_BOTTOM,
                (RectComponent.MousePosition.X_MIDDLE, RectComponent.MousePosition.Y_BOTTOM):
                RectComponent.Mode.RESIZE_BOTTOM,
                (RectComponent.MousePosition.X_LEFT, RectComponent.MousePosition.Y_NEAR_BOTTOM):
                RectComponent.Mode.RESIZE_LEFT_BOTTOM,
                (RectComponent.MousePosition.X_LEFT, RectComponent.MousePosition.Y_BOTTOM):
                RectComponent.Mode.RESIZE_LEFT_BOTTOM,
                (RectComponent.MousePosition.X_NEAR_LEFT, RectComponent.MousePosition.Y_BOTTOM):
                RectComponent.Mode.RESIZE_LEFT_BOTTOM,
                (RectComponent.MousePosition.X_LEFT, RectComponent.MousePosition.Y_MIDDLE):
                RectComponent.Mode.RESIZE_LEFT,
                }.get((x_pos, y_pos), RectComponent.Mode.NO_ACTION)

    @change_rect_and_pos
    def _resize_at_any_mode(self, pos: QPointF) -> Tuple[float, float]:
        """
        :param pos: mouse position.
        :return: new component width and height.
        """

        width = abs(pos.x() - self._x_fixed)
        height = abs(pos.y() - self._y_fixed)
        return width, height

    @change_rect_and_pos
    def _resize_at_bottom_and_top_mode(self, pos: QPointF) -> Tuple[float, float]:
        """
        :param pos: mouse position.
        :return: new component width and height.
        """

        width = self.rect().width()
        height = abs(pos.y() - self._y_fixed)
        return width, height

    @change_rect_and_pos
    def _resize_at_left_and_right_mode(self, pos: QPointF) -> Tuple[float, float]:
        """
        :param pos: mouse position.
        :return: new component width and height.
        """

        width = abs(pos.x() - self._x_fixed)
        height = self.rect().height()
        return width, height

    def _set_cursor(self) -> None:
        self.setCursor(RectComponent.CURSORS.get(self._mode, Qt.ArrowCursor))

    def check_big_enough(self) -> bool:
        """
        :return: if True, then the component is larger than the allowed minimum size.
        """

        return self.rect().width() >= self.MIN_SIZE and self.rect().height() >= self.MIN_SIZE

    def check_in_resize_mode(self) -> bool:
        """
        :return: True if the component is in resizing mode.
        """

        return self._mode not in (RectComponent.Mode.MOVE, RectComponent.Mode.NO_ACTION)

    def contains_point(self, point: Union[PointComponent, QPointF]) -> bool:
        """
        :param point: point to check.
        :return: True if the point is inside the rectangle.
        """

        pos = point.pos() if isinstance(point, PointComponent) else point
        return self.contains(self.mapFromScene(pos))

    def convert_to_json(self) -> Dict[str, Any]:
        """
        :return: dictionary with basic object attributes.
        """

        return {**super().convert_to_json(),
                "brush_color": self.brush().color().rgba(),
                "brush_style": self.brush().style(),
                "pen_color": self._pen.color().rgba(),
                "pen_width": self._pen.widthF(),
                "rect": (self.rect().x(), self.rect().y(), self.rect().width(), self.rect().height())}

    def copy(self) -> Tuple["RectComponent", QPointF]:
        """
        :return: copied component and its current position.
        """

        component = RectComponent(QRectF(self.rect()), QPen(self._pen), self._update_pen_for_selection, self._draggable,
                                  self._selectable, self._unique_selection)
        component.setBrush(self.brush())
        return component, self.scenePos()

    def fix_mode(self, mode: Mode) -> None:
        """
        :param mode: new mode that will be fixed for the component.
        """

        self._mode = mode
        if self._mode == RectComponent.Mode.RESIZE_ANY:
            self._x_fixed, self._y_fixed = self.pos().x(), self.pos().y()
        elif self._mode == RectComponent.Mode.RESIZE_BOTTOM:
            self._x_fixed, self._y_fixed = None, self.pos().y()
        elif self._mode == RectComponent.Mode.RESIZE_LEFT:
            self._x_fixed, self._y_fixed = self.pos().x() + self.rect().width(), None
        elif self._mode == RectComponent.Mode.RESIZE_LEFT_BOTTOM:
            self._x_fixed, self._y_fixed = self.pos().x() + self.rect().width(), self.pos().y()
        elif self._mode == RectComponent.Mode.RESIZE_LEFT_TOP:
            self._x_fixed, self._y_fixed = self.pos().x() + self.rect().width(), self.pos().y() + self.rect().height()
        elif self._mode == RectComponent.Mode.RESIZE_RIGHT:
            self._x_fixed, self._y_fixed = self.pos().x(), None
        elif self._mode == RectComponent.Mode.RESIZE_RIGHT_BOTTOM:
            self._x_fixed, self._y_fixed = self.pos().x(), self.pos().y()
        elif self._mode == RectComponent.Mode.RESIZE_RIGHT_TOP:
            self._x_fixed, self._y_fixed = self.pos().x(), self.pos().y() + self.rect().height()
        elif self._mode == RectComponent.Mode.RESIZE_TOP:
            self._x_fixed, self._y_fixed = None, self.pos().y() + self.rect().height()

    def go_to_resize_mode(self) -> None:
        self.setFlag(QGraphicsItem.ItemIsMovable, False)
        self.fix_mode(self._mode)

    def hoverEnterEvent(self, event: QGraphicsSceneHoverEvent) -> None:
        """
        :param event: hover event.
        """

        self._mode = self._determine_mode(event.pos())
        self._set_cursor()

    def hoverMoveEvent(self, event: QGraphicsSceneHoverEvent) -> None:
        """
        :param event: hover event.
        """

        self._mode = self._determine_mode(event.pos())
        self._set_cursor()

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: QWidget) -> None:
        """
        :param painter: painter;
        :param option: option parameter provides style options for the item, such as its state, exposed area and its
        level-of-detail hints;
        :param widget: this argument is optional. If provided, it points to the widget that is being painted on;
        otherwise, it is 0. For cached painting, widget is always 0.
        """

        if option.state & QStyle.State_Selected:
            option.state &= not QStyle.State_Selected
        super().paint(painter, option, widget)

    def resize_by_mouse(self, pos: QPointF) -> None:
        """
        :param pos: mouse position.
        """

        if self._mode in (RectComponent.Mode.RESIZE_ANY, RectComponent.Mode.RESIZE_LEFT_BOTTOM,
                          RectComponent.Mode.RESIZE_LEFT_TOP, RectComponent.Mode.RESIZE_RIGHT_BOTTOM,
                          RectComponent.Mode.RESIZE_RIGHT_TOP):
            self._resize_at_any_mode(pos)
        elif self._mode in (RectComponent.Mode.RESIZE_BOTTOM, RectComponent.Mode.RESIZE_TOP):
            self._resize_at_bottom_and_top_mode(pos)
        elif self._mode in (RectComponent.Mode.RESIZE_LEFT, RectComponent.Mode.RESIZE_RIGHT):
            self._resize_at_left_and_right_mode(pos)

    def resize_to_include_rect(self, rect: QRectF) -> None:
        """
        :param rect: rectangle that should be inside RectComponent.
        """

        current_rect_at_scene = self.mapRectToScene(self.rect())
        for rect_vertex in (rect.topLeft(), rect.topRight(), rect.bottomRight(), rect.bottomLeft()):
            if not current_rect_at_scene.contains(rect_vertex):
                break
        else:
            return

        left = min(rect.left(), current_rect_at_scene.left())
        right = max(rect.right(), current_rect_at_scene.right())
        top = min(rect.top(), current_rect_at_scene.top())
        bottom = max(rect.bottom(), current_rect_at_scene.bottom())
        self.setRect(QRectF(0, 0, right - left, bottom - top))
        self.setPos(left, top)

    def set_pen(self, pen: QPen) -> None:
        """
        :param pen: new pen.
        """

        self._pen = pen
        self.setPen(pen)

    def update_selection(self) -> None:
        if self.is_selected():
            pen = self._pen if self._update_pen_for_selection is None else self._update_pen_for_selection()
            super().setPen(pen)
        elif self.pen() != self._pen:
            super().setPen(QPen(self._pen))
