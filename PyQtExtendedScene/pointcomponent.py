from typing import Optional, Tuple
from PyQt5.QtCore import QPointF
from PyQt5.QtGui import QBrush, QColor, QPainter, QPen
from PyQt5.QtWidgets import QGraphicsEllipseItem, QGraphicsItem, QStyle, QStyleOptionGraphicsItem, QWidget
from .sender import Sender


class PointComponent(QGraphicsEllipseItem):
    """
    Point component that can be drawn and moved.
    """

    PEN_COLOR: QColor = QColor("#0047AB")
    PEN_WIDTH: float = 2

    def __init__(self, r: Optional[float] = None, r_selected: Optional[float] = None, pen: Optional[QPen] = None,
                 draggable: bool = True, selectable: bool = True, unique_selection: bool = False) -> None:
        """
        :param r: point radius;
        :param pen: pen;
        :param draggable: True if component can be dragged;
        :param selectable: True if component can be selected;
        :param unique_selection: True if selecting this component should reset all others selections
        ('selectable' must be set).
        """

        super().__init__()
        self._draggable: bool = draggable
        self._r: Optional[float] = r
        self._r_selected: Optional[float] = r_selected
        self._scale_factor: float = 1
        self._selectable: bool = selectable
        self._selection_signal: Sender = Sender()
        self._selection_signal.connect(self.handle_selection)
        self._unique_selection: bool = unique_selection

        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.ItemIsMovable, draggable)
        self.setFlag(QGraphicsItem.ItemIsSelectable, selectable)

        self.setPen(pen)
        self._set_rect(r)

    def _set_rect(self, r: Optional[float]) -> None:
        """
        :param r: point radius.
        """

        if r is not None:
            r /= self._scale_factor
            self.setRect(-r, -r, 2 * r, 2 * r)

    def copy(self) -> Tuple["PointComponent", QPointF]:
        """
        :return: copied component and its current position.
        """

        component = PointComponent(self._r, self._r_selected, self.pen(), self._draggable, self._selectable,
                                   self._unique_selection)
        component.setBrush(self.brush())
        return component, self.pos()

    def handle_selection(self, selected: bool = True) -> None:
        """
        :param selected: if selected is True and this item is selectable, this item is selected; otherwise, it is
        unselected.
        """

        self._set_rect(self._r_selected if selected else self._r)

    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value):
        """
        :param change: the parameter of the item that is changing;
        :param value: the new value, the type of the value depends on change.
        """

        if change == QGraphicsItem.GraphicsItemChange.ItemSelectedChange:
            self._selection_signal.emit(value)

        return super().itemChange(change, value)

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

    def setPen(self, pen: Optional[QPen] = None) -> None:
        """
        :param pen: pen.
        """

        pen = QPen(pen or QPen(QBrush(PointComponent.PEN_COLOR), PointComponent.PEN_WIDTH))
        pen.setCosmetic(True)
        super().setPen(pen)

    def update_scale(self, scale_factor: float) -> None:
        """
        :param scale_factor: new scale factor.
        """

        self._scale_factor = scale_factor
        self._set_rect(self._r_selected if self.isSelected() else self._r)
