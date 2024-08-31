import time
from enum import auto, Enum
from typing import Optional
from PyQt5.QtCore import QPointF, QRectF, Qt
from PyQt5.QtGui import QBrush, QColor, QPainter, QPen
from PyQt5.QtWidgets import (QGraphicsItem, QGraphicsRectItem, QGraphicsSceneHoverEvent, QStyle,
                             QStyleOptionGraphicsItem, QWidget)


class Mode(Enum):
    MOVE_BOTTOM = auto()
    MOVE_LEFT = auto()
    MOVE_RIGHT = auto()
    MOVE_TOP = auto()
    NO = auto()
    RESIZE = auto()


class ScalableComponent(QGraphicsRectItem):
    """
    Rectangular component that can be drawn with the mouse and resized.
    """

    CURSORS = {Mode.MOVE_BOTTOM: Qt.SizeVerCursor,
               Mode.MOVE_LEFT: Qt.SizeHorCursor,
               Mode.MOVE_RIGHT: Qt.SizeHorCursor,
               Mode.MOVE_TOP: Qt.SizeVerCursor,
               Mode.NO: Qt.ArrowCursor}

    def __init__(self, rect: Optional[QRectF] = None, pen_color: Optional[QColor] = None,
                 pen_width: Optional[float] = None, draggable: bool = True, selectable: bool = True,
                 unique_selection: bool = True) -> None:
        """
        :param rect:
        :param pen_color:
        :param pen_width:
        :param draggable: True if component can be dragged;
        :param selectable: True if component can be selected;
        :param unique_selection: True if selecting this component should reset all others selections
        ('selectable' must be set).
        """

        super().__init__()
        self._draggable: bool = draggable
        self._mode: Mode = Mode.NO
        self._selectable: bool = selectable
        self._solid_pen: QPen = QPen()
        self._unique_selection: bool = unique_selection

        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.ItemIsMovable, draggable)
        self.setFlag(QGraphicsItem.ItemIsSelectable, selectable)
        self.setPen(pen_color, pen_width)
        if rect:
            self.setRect(rect)

    @property
    def draggable(self) -> bool:
        """
        :return: True if component can be dragged.
        """

        return self._draggable

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

    def _get_mode(self, pos: QPointF) -> Mode:
        """
        :param pos:
        :return:
        """

        x, y = pos.x(), pos.y()
        pen_width = self.pen().width()
        left = self.rect().x()
        right = left + self.rect().width()
        top = self.rect().y()
        bottom = top + self.rect().height()
        if top <= y <= bottom:
            if left - pen_width <= x <= left + pen_width / 2:
                return Mode.MOVE_LEFT

            if right - pen_width / 2 <= x <= right + pen_width:
                return Mode.MOVE_RIGHT

        if left <= x <= right:
            if top - pen_width <= y <= top + pen_width / 2:
                return Mode.MOVE_TOP

            if bottom - pen_width / 2 <= y <= bottom + pen_width:
                return Mode.MOVE_BOTTOM

        return Mode.NO

    def _set_cursor(self) -> None:
        self.setCursor(ScalableComponent.CURSORS.get(self._mode, Qt.ArrowCursor))

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

        self._solid_pen = create_solid_pen(color, width)
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


def create_solid_pen(color: QColor, width: float) -> QPen:
    """
    :param color: pen color;
    :param width: pen width.
    :return: solid pen.
    """

    color = color or "red"
    width = width or 1
    return QPen(QBrush(QColor(color)), width)


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
