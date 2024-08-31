import time
from typing import Optional
from PyQt5.QtCore import QRectF, Qt
from PyQt5.QtGui import QBrush, QColor, QPen
from PyQt5.QtWidgets import QGraphicsItem, QGraphicsRectItem, QStyle


class ScalableComponent(QGraphicsRectItem):
    """
    Rectangular component that can be drawn with the mouse and resized.
    """

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
        self._selectable: bool = selectable
        self._solid_pen: QPen = QPen()
        self._unique_selection: bool = unique_selection

        self.setFlags(QGraphicsItem.ItemIsMovable | QGraphicsItem.ItemIsSelectable)
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

    def paint(self, painter, option, widget = ...) -> None:
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
