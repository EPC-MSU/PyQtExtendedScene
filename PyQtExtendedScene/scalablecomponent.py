import time
from enum import auto, Enum
from typing import Optional
from PyQt5.QtCore import QPointF, QRectF, Qt
from PyQt5.QtGui import QBrush, QColor, QPainter, QPen
from PyQt5.QtWidgets import (QGraphicsItem, QGraphicsRectItem, QGraphicsSceneHoverEvent, QStyle,
                             QStyleOptionGraphicsItem, QWidget)


class Mode(Enum):
    MOVE = auto()
    NO = auto()
    RESIZE_BOTTOM = auto()
    RESIZE_LEFT = auto()
    RESIZE_LEFT_BOTTOM = auto()
    RESIZE_LEFT_TOP = auto()
    RESIZE_RIGHT = auto()
    RESIZE_RIGHT_BOTTOM = auto()
    RESIZE_RIGHT_TOP = auto()
    RESIZE_TOP = auto()


class ScalableComponent(QGraphicsRectItem):
    """
    Rectangular component that can be drawn with the mouse and resized.
    """

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
    PEN_COLOR: str = "#0047AB"
    PEN_WIDTH: float = 2

    def __init__(self, rect: Optional[QRectF] = None, pen_color: Optional[QColor] = None,
                 pen_width: Optional[float] = None, draggable: bool = True, selectable: bool = True,
                 unique_selection: bool = False) -> None:
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
    def mode(self) -> Mode:
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
    def _create_solid_pen(color: QColor, width: float) -> QPen:
        """
        :param color: pen color;
        :param width: pen width.
        :return: solid pen.
        """

        color = color or ScalableComponent.PEN_COLOR
        width = width or ScalableComponent.PEN_WIDTH
        return QPen(QBrush(QColor(color)), width)

    def _get_mode(self, pos: QPointF) -> Mode:
        """
        :param pos: mouse position.
        :return: mode.
        """

        if len(self.scene().selectedItems()) == 1 and self.isSelected():
            return self._get_mode_by_position(pos)

        return Mode.NO

    def _get_mode_by_position(self, pos: QPointF) -> Mode:
        """
        :param pos: mouse position.
        :return: mode.
        """

        x, y = pos.x(), pos.y()
        pen_width = self.pen().width()
        left = self.rect().x()
        width = self.rect().width()
        right = left + width
        top = self.rect().y()
        height = self.rect().height()
        bottom = top + height

        if top <= y <= top + ScalableComponent.DIAG_PORTION * height:
            if left - pen_width <= x <= left + pen_width / 2:
                return Mode.RESIZE_LEFT_TOP

            if right - pen_width / 2 <= x <= right + pen_width:
                return Mode.RESIZE_RIGHT_TOP

        if top + ScalableComponent.DIAG_PORTION * height < y < bottom - ScalableComponent.DIAG_PORTION * height:
            if left - pen_width <= x <= left + pen_width / 2:
                return Mode.RESIZE_LEFT

            if right - pen_width / 2 <= x <= right + pen_width:
                return Mode.RESIZE_RIGHT

        if bottom - ScalableComponent.DIAG_PORTION * height <= y <= bottom:
            if left - pen_width <= x <= left + pen_width / 2:
                return Mode.RESIZE_LEFT_BOTTOM

            if right - pen_width / 2 <= x <= right + pen_width:
                return Mode.RESIZE_RIGHT_BOTTOM

        if left <= x <= left + ScalableComponent.DIAG_PORTION * width:
            if top - pen_width <= y <= top + pen_width / 2:
                return Mode.RESIZE_LEFT_TOP

            if bottom - pen_width / 2 <= y <= bottom + pen_width:
                return Mode.RESIZE_LEFT_BOTTOM

        if left + ScalableComponent.DIAG_PORTION * width < x < right - ScalableComponent.DIAG_PORTION * width:
            if top - pen_width <= y <= top + pen_width / 2:
                return Mode.RESIZE_TOP

            if bottom - pen_width / 2 <= y <= bottom + pen_width:
                return Mode.RESIZE_BOTTOM

        if right - ScalableComponent.DIAG_PORTION * width <= x <= right:
            if top - pen_width <= y <= top + pen_width / 2:
                return Mode.RESIZE_RIGHT_TOP

            if bottom - pen_width / 2 <= y <= bottom + pen_width:
                return Mode.RESIZE_RIGHT_BOTTOM

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
