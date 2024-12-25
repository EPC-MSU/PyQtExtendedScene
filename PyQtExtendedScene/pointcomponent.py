from typing import Any, Dict, Optional, Tuple
from PyQt5.QtCore import QPointF
from PyQt5.QtGui import QBrush, QColor, QPainter, QPen
from PyQt5.QtWidgets import QGraphicsEllipseItem, QStyle, QStyleOptionGraphicsItem, QWidget
from . import utils as ut
from .basecomponent import BaseComponent


class PointComponent(QGraphicsEllipseItem, BaseComponent):
    """
    Point component that can be drawn and moved.
    """

    INCREASE_FACTOR: float = 2
    PEN_COLOR: QColor = QColor("#0047AB")
    PEN_WIDTH: float = 2
    RADIUS: float = 4
    Z_VALUE: float = 2

    def __init__(self, radius: Optional[float] = None, pen: Optional[QPen] = None, scale: Optional[float] = None,
                 increase_factor: Optional[float] = None, draggable: bool = True, selectable: bool = True,
                 unique_selection: bool = False) -> None:
        """
        :param radius: point radius;
        :param pen: pen;
        :param scale: scale factor;
        :param draggable: True if component can be dragged;
        :param selectable: True if component can be selected;
        :param unique_selection: True if selecting this component should reset all others selections
        ('selectable' must be set).
        """

        QGraphicsEllipseItem.__init__(self)
        BaseComponent.__init__(self, draggable, selectable, unique_selection)

        self._increase_factor: float = increase_factor or self.INCREASE_FACTOR
        self._r: float = radius or self.RADIUS
        self._scale_factor: float = scale or 1

        self.setPen(pen or ut.create_cosmetic_pen(self.PEN_COLOR, self.PEN_WIDTH))
        self.setZValue(self.Z_VALUE)
        self._set_rect(self._r)

    @classmethod
    def create_from_json(cls, data: Dict[str, Any]) -> "PointComponent":
        """
        :param data: a dictionary with basic attributes that can be used to create an object.
        :return: class instance.
        """

        pen = QPen(QBrush(QColor(data["pen_color"])), data["pen_width"])
        component = PointComponent(data["radius"], pen, draggable=data["draggable"], selectable=data["selectable"],
                                   unique_selection=data["unique_selection"])
        component.setBrush(QBrush(QColor(data["brush_color"]), data["brush_style"]))
        return component

    def _set_rect(self, radius: Optional[float]) -> None:
        """
        :param radius: point radius.
        """

        if radius is not None:
            radius /= self._scale_factor
            self.setRect(-radius, -radius, 2 * radius, 2 * radius)

    def convert_to_json(self) -> Dict[str, Any]:
        """
        :return: dictionary with basic object attributes.
        """

        return {**super().convert_to_json(),
                "brush_color": self.brush().color().rgba(),
                "brush_style": self.brush().style(),
                "pen_color": self.pen().color().rgba(),
                "pen_width": self.pen().widthF(),
                "radius": self._r}

    def copy(self) -> Tuple["PointComponent", QPointF]:
        """
        :return: copied component and its current position.
        """

        component = PointComponent(self._r, self.pen(), draggable=self._draggable, selectable=self._selectable,
                                   unique_selection=self._unique_selection)
        component.setBrush(self.brush())
        return component, self.scenePos()

    def handle_selection(self, selected: bool = True) -> None:
        """
        :param selected: if selected is True and this item is selectable, this item is selected; otherwise, it is
        unselected.
        """

        self._set_rect(self._r * self.INCREASE_FACTOR if selected else self._r)

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

    def update_scale(self, scale_factor: float) -> None:
        """
        :param scale_factor: new scale factor.
        """

        super().update_scale(scale_factor)
        self._set_rect(self._r * self.INCREASE_FACTOR if self._r is not None and self.is_selected() else self._r)
