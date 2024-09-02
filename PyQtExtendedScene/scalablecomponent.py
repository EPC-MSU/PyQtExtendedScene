import time
from enum import auto, Enum
from typing import Callable, Optional, Tuple
from PyQt5.QtCore import QPointF, QRectF, Qt
from PyQt5.QtGui import QBrush, QColor, QPainter, QPen
from PyQt5.QtWidgets import (QGraphicsItem, QGraphicsRectItem, QGraphicsSceneHoverEvent, QStyle,
                             QStyleOptionGraphicsItem, QWidget)


def change_rect_and_pos(func: Callable[[QPointF], Tuple[float, float]]):
    """
    Decorator changes the position and size of the scalable component.
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


class ScalableComponent(QGraphicsRectItem):
    """
    Rectangular component that can be drawn with the mouse and resized.
    """

    class Mode(Enum):
        """
        Enumerates the modes in which the component can be.
        """

        MOVE = auto()  # moving a component
        NO = auto()
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

    CURSORS = {Mode.MOVE: Qt.SizeAllCursor,
               Mode.NO: Qt.ArrowCursor,
               Mode.RESIZE_BOTTOM: Qt.SizeVerCursor,
               Mode.RESIZE_LEFT: Qt.SizeHorCursor,
               Mode.RESIZE_LEFT_BOTTOM: Qt.SizeBDiagCursor,
               Mode.RESIZE_LEFT_TOP: Qt.SizeFDiagCursor,
               Mode.RESIZE_RIGHT: Qt.SizeHorCursor,
               Mode.RESIZE_RIGHT_BOTTOM: Qt.SizeFDiagCursor,
               Mode.RESIZE_RIGHT_TOP: Qt.SizeBDiagCursor,
               Mode.RESIZE_TOP: Qt.SizeVerCursor}
    DIAG_PORTION: float = 0.05
    MIN_SIZE: float = 2
    PEN_COLOR: QColor = QColor("#0047AB")
    PEN_WIDTH: float = 2

    def __init__(self, rect: Optional[QRectF] = None, pen_color: Optional[QColor] = None,
                 pen_width: Optional[float] = None, draggable: bool = True, selectable: bool = True,
                 unique_selection: bool = False) -> None:
        """
        :param rect: rect for component;
        :param pen_color: pen color;
        :param pen_width: pen width;
        :param draggable: True if component can be dragged;
        :param selectable: True if component can be selected;
        :param unique_selection: True if selecting this component should reset all others selections
        ('selectable' must be set).
        """

        super().__init__()
        self._draggable: bool = draggable
        self._mode: ScalableComponent.Mode = ScalableComponent.Mode.NO
        self._selectable: bool = selectable
        self._solid_pen: QPen = QPen()
        self._unique_selection: bool = unique_selection
        self._x_fixed: Optional[float] = None
        self._y_fixed: Optional[float] = None

        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.ItemIsMovable, draggable)
        self.setFlag(QGraphicsItem.ItemIsSelectable, selectable)
        self.setPen(pen_color, pen_width)
        if rect is not None:
            self.setRect(rect)

    @property
    def draggable(self) -> bool:
        """
        :return: True if component can be dragged.
        """

        return self._draggable

    @property
    def mode(self) -> "Mode":
        """
        :return: mode the component is in. The component can be in move or resize mode.
        """

        return self._mode

    @property
    def selectable(self) -> bool:
        """
        :return: True if component can be selected.
        """

        return self._selectable

    @property
    def unique_selection(self) -> bool:
        """
        :return: True if selecting this component should reset all others selections.
        """

        return self._unique_selection

    @staticmethod
    def _create_solid_pen(color: Optional[QColor] = None, width: Optional[float] = None) -> QPen:
        """
        :param color: pen color;
        :param width: pen width.
        :return: solid pen.
        """

        color = color or ScalableComponent.PEN_COLOR
        width = width or ScalableComponent.PEN_WIDTH
        return QPen(QBrush(color), width)

    def _get_mode(self, pos: QPointF) -> Mode:
        """
        :param pos: mouse position.
        :return: mode.
        """

        if len(self.scene().selectedItems()) == 1 and self.isSelected():
            return self._get_mode_by_mouse_position(pos)

        return ScalableComponent.Mode.NO

    def _get_mode_by_mouse_position(self, pos: QPointF) -> Mode:
        """
        :param pos: mouse position.
        :return: mode.
        """

        x, y = pos.x(), pos.y()
        pen_width = self.pen().width()
        left = self.boundingRect().x()
        width = self.boundingRect().width()
        right = self.boundingRect().right()
        top = self.boundingRect().y()
        height = self.boundingRect().height()
        bottom = self.boundingRect().bottom()

        x_pos = None
        if left <= x <= left + pen_width:
            x_pos = ScalableComponent.MousePosition.X_LEFT
        elif left <= x <= left + ScalableComponent.DIAG_PORTION * width:
            x_pos = ScalableComponent.MousePosition.X_NEAR_LEFT
        elif left + ScalableComponent.DIAG_PORTION * width < x < right - ScalableComponent.DIAG_PORTION * width:
            x_pos = ScalableComponent.MousePosition.X_MIDDLE
        elif right - pen_width <= x <= right:
            x_pos = ScalableComponent.MousePosition.X_RIGHT
        elif right - ScalableComponent.DIAG_PORTION * width <= x <= right:
            x_pos = ScalableComponent.MousePosition.X_NEAR_RIGHT

        y_pos = None
        if top <= y <= top + pen_width:
            y_pos = ScalableComponent.MousePosition.Y_TOP
        elif top <= y <= top + ScalableComponent.DIAG_PORTION * height:
            y_pos = ScalableComponent.MousePosition.Y_NEAR_TOP
        elif top + ScalableComponent.DIAG_PORTION * height < y < bottom - ScalableComponent.DIAG_PORTION * height:
            y_pos = ScalableComponent.MousePosition.Y_MIDDLE
        elif bottom - pen_width <= y <= bottom:
            y_pos = ScalableComponent.MousePosition.Y_BOTTOM
        elif bottom - ScalableComponent.DIAG_PORTION * height <= y <= bottom:
            y_pos = ScalableComponent.MousePosition.Y_NEAR_BOTTOM

        return {(ScalableComponent.MousePosition.X_LEFT, ScalableComponent.MousePosition.Y_NEAR_TOP):
                ScalableComponent.Mode.RESIZE_LEFT_TOP,
                (ScalableComponent.MousePosition.X_LEFT, ScalableComponent.MousePosition.Y_TOP):
                ScalableComponent.Mode.RESIZE_LEFT_TOP,
                (ScalableComponent.MousePosition.X_NEAR_LEFT, ScalableComponent.MousePosition.Y_TOP):
                ScalableComponent.Mode.RESIZE_LEFT_TOP,
                (ScalableComponent.MousePosition.X_MIDDLE, ScalableComponent.MousePosition.Y_TOP):
                ScalableComponent.Mode.RESIZE_TOP,
                (ScalableComponent.MousePosition.X_RIGHT, ScalableComponent.MousePosition.Y_NEAR_TOP):
                ScalableComponent.Mode.RESIZE_RIGHT_TOP,
                (ScalableComponent.MousePosition.X_RIGHT, ScalableComponent.MousePosition.Y_TOP):
                ScalableComponent.Mode.RESIZE_RIGHT_TOP,
                (ScalableComponent.MousePosition.X_NEAR_RIGHT, ScalableComponent.MousePosition.Y_TOP):
                ScalableComponent.Mode.RESIZE_RIGHT_TOP,
                (ScalableComponent.MousePosition.X_RIGHT, ScalableComponent.MousePosition.Y_MIDDLE):
                ScalableComponent.Mode.RESIZE_RIGHT,
                (ScalableComponent.MousePosition.X_RIGHT, ScalableComponent.MousePosition.Y_NEAR_BOTTOM):
                ScalableComponent.Mode.RESIZE_RIGHT_BOTTOM,
                (ScalableComponent.MousePosition.X_RIGHT, ScalableComponent.MousePosition.Y_BOTTOM):
                ScalableComponent.Mode.RESIZE_RIGHT_BOTTOM,
                (ScalableComponent.MousePosition.X_NEAR_RIGHT, ScalableComponent.MousePosition.Y_BOTTOM):
                ScalableComponent.Mode.RESIZE_RIGHT_BOTTOM,
                (ScalableComponent.MousePosition.X_MIDDLE, ScalableComponent.MousePosition.Y_BOTTOM):
                ScalableComponent.Mode.RESIZE_BOTTOM,
                (ScalableComponent.MousePosition.X_LEFT, ScalableComponent.MousePosition.Y_NEAR_BOTTOM):
                ScalableComponent.Mode.RESIZE_LEFT_BOTTOM,
                (ScalableComponent.MousePosition.X_LEFT, ScalableComponent.MousePosition.Y_BOTTOM):
                ScalableComponent.Mode.RESIZE_LEFT_BOTTOM,
                (ScalableComponent.MousePosition.X_NEAR_LEFT, ScalableComponent.MousePosition.Y_BOTTOM):
                ScalableComponent.Mode.RESIZE_LEFT_BOTTOM,
                (ScalableComponent.MousePosition.X_LEFT, ScalableComponent.MousePosition.Y_MIDDLE):
                ScalableComponent.Mode.RESIZE_LEFT,
                }.get((x_pos, y_pos), ScalableComponent.Mode.NO)

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
        self.setCursor(ScalableComponent.CURSORS.get(self._mode, Qt.ArrowCursor))

    def check_big_enough(self) -> bool:
        """
        :return: if True, then the component is larger than the allowed minimum size.
        """

        return self.rect().width() >= ScalableComponent.MIN_SIZE and self.rect().height() >= ScalableComponent.MIN_SIZE

    def copy(self) -> Tuple["ScalableComponent", QPointF]:
        """
        :return: copied component and its current position.
        """

        pen_color = self._solid_pen.color()
        pen_width = self._solid_pen.widthF()
        component = ScalableComponent(QRectF(self.rect()), pen_color, pen_width, self.draggable, self.selectable,
                                      self.unique_selection)
        return component, self.pos()

    def fix_mode(self, mode: Mode) -> None:
        """
        :param mode: new mode.
        """

        self._mode = mode
        if self._mode == ScalableComponent.Mode.RESIZE_ANY:
            self._x_fixed, self._y_fixed = self.pos().x(), self.pos().y()
        elif self._mode == ScalableComponent.Mode.RESIZE_BOTTOM:
            self._x_fixed, self._y_fixed = None, self.pos().y()
        elif self._mode == ScalableComponent.Mode.RESIZE_LEFT:
            self._x_fixed, self._y_fixed = self.pos().x() + self.rect().width(), None
        elif self._mode == ScalableComponent.Mode.RESIZE_LEFT_BOTTOM:
            self._x_fixed, self._y_fixed = self.pos().x() + self.rect().width(), self.pos().y()
        elif self._mode == ScalableComponent.Mode.RESIZE_LEFT_TOP:
            self._x_fixed, self._y_fixed = self.pos().x() + self.rect().width(), self.pos().y() + self.rect().height()
        elif self._mode == ScalableComponent.Mode.RESIZE_RIGHT:
            self._x_fixed, self._y_fixed = self.pos().x(), None
        elif self._mode == ScalableComponent.Mode.RESIZE_RIGHT_BOTTOM:
            self._x_fixed, self._y_fixed = self.pos().x(), self.pos().y()
        elif self._mode == ScalableComponent.Mode.RESIZE_RIGHT_TOP:
            self._x_fixed, self._y_fixed = self.pos().x(), self.pos().y() + self.rect().height()
        elif self._mode == ScalableComponent.Mode.RESIZE_TOP:
            self._x_fixed, self._y_fixed = None, self.pos().y() + self.rect().height()

    def hoverEnterEvent(self, event: QGraphicsSceneHoverEvent) -> None:
        self._mode = self._get_mode(event.pos())
        self._set_cursor()

    def hoverMoveEvent(self, event: QGraphicsSceneHoverEvent) -> None:
        self._mode = self._get_mode(event.pos())
        self._set_cursor()

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: QWidget) -> None:
        if option.state & QStyle.State_Selected:
            option.state &= not QStyle.State_Selected
        super().paint(painter, option, widget)

    def resize_by_mouse(self, pos: QPointF) -> None:
        """
        :param pos: mouse position.
        """

        if self._mode in (ScalableComponent.Mode.RESIZE_ANY, ScalableComponent.Mode.RESIZE_LEFT_BOTTOM,
                          ScalableComponent.Mode.RESIZE_LEFT_TOP, ScalableComponent.Mode.RESIZE_RIGHT_BOTTOM,
                          ScalableComponent.Mode.RESIZE_RIGHT_TOP):
            self._resize_at_any_mode(pos)
        elif self._mode in (ScalableComponent.Mode.RESIZE_BOTTOM, ScalableComponent.Mode.RESIZE_TOP):
            self._resize_at_bottom_and_top_mode(pos)
        elif self._mode in (ScalableComponent.Mode.RESIZE_LEFT, ScalableComponent.Mode.RESIZE_RIGHT):
            self._resize_at_left_and_right_mode(pos)

    def select(self, selected: bool = True) -> None:
        """
        :param selected: if selected is True and this item is selectable, this item is selected; otherwise, it is
        unselected.
        """

        self.setSelected(selected)
        pen = get_dashed_pen(self._solid_pen) if self.isSelected() else QPen(self._solid_pen)
        super().setPen(pen)

    def setPen(self, color: Optional[QColor] = None, width: Optional[float] = None) -> None:
        """
        :param color: pen color;
        :param width: pen width.
        """

        self._solid_pen = self._create_solid_pen(color, width)
        super().setPen(QPen(self._solid_pen))

    @staticmethod
    def update_scale(scale: float) -> None:
        """
        :param scale: new scale.
        """

        ...

    def update_selection(self) -> None:
        if self.isSelected():
            super().setPen(get_dashed_pen(self._solid_pen))
        elif self.pen() != self._solid_pen:
            super().setPen(QPen(self._solid_pen))


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
