import time
from typing import Optional
from PyQt5.QtCore import QRectF, Qt
from PyQt5.QtGui import QBrush, QColor, QPen
from PyQt5.QtWidgets import QGraphicsRectItem
from .abstractcomponent import AbstractComponent


class ScalableComponent(AbstractComponent):

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

        super().__init__(draggable, selectable, unique_selection)
        self._item: QGraphicsRectItem = QGraphicsRectItem(self)
        self._pen: QPen = QPen()
        self.set_pen(pen_color, pen_width)
        self._selected: bool = False

        if rect:
            self.set_rect(rect)

    @staticmethod
    def _create_pen(color: QColor, width: float) -> QPen:
        color = color or "red"
        width = width or 1
        return QPen(QBrush(QColor(color)), width)

    def _get_selection_pen(self) -> QPen:
        pen = QPen(self._pen)
        pen.setStyle(Qt.CustomDashLine)
        pattern = (0, 3, 0, 3, 3, 0, 3, 0)
        update_interval = 0.4
        mod = int(time.monotonic() / update_interval) % (len(pattern) // 2)
        pen.setDashPattern(pattern[mod * 2:] + pattern[:mod * 2])
        return pen

    def select(self, selected: bool = True) -> None:
        self._selected = selected
        if selected:
            pen = self._get_selection_pen()
        else:
            pen = QPen(self._pen)
        self._item.setPen(pen)

    def set_pen(self, color: Optional[QColor] = None, width: Optional[float] = None) -> None:
        self._pen = self._create_pen(color, width)
        self._item.setPen(self._pen)

    def set_rect(self, rect: QRectF) -> None:
        self.setPos(rect.x(), rect.y())
        self._item.setRect(0, 0, rect.width(), rect.height())

    def update_scale(self, scale: float) -> None:
        """
        :param scale: new scale.
        """

        pen = QPen(self._item.pen())
        pen.setWidthF(self._pen.widthF() * scale)
        self._item.setPen(pen)

    def update_selection(self) -> None:
        if self._selected:
            self._item.setPen(self._get_selection_pen())
