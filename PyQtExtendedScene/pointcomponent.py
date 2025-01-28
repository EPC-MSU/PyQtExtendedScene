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
    RADIUS: float = 4
    Z_VALUE: float = 2

    def __init__(self, radius: Optional[float] = None, pen: Optional[QPen] = None, brush: Optional[QBrush] = None,
                 scale: Optional[float] = None, increase_factor: Optional[float] = None, draggable: bool = True,
                 selectable: bool = True, unique_selection: bool = False) -> None:
        """
        :param radius: point radius;
        :param pen: pen for component;
        :param brush: brush for component;
        :param scale: scale factor;
        :param increase_factor: point radius increase factor when selecting a point;
        :param draggable: True if component can be dragged;
        :param selectable: True if component can be selected;
        :param unique_selection: True if selecting this component should reset all others selections
        ('selectable' must be set).
        """

        QGraphicsEllipseItem.__init__(self)
        BaseComponent.__init__(self, pen, brush, draggable, selectable, unique_selection)

        self._increase_factor: float = increase_factor or self.INCREASE_FACTOR
        self._r: float = radius or self.RADIUS
        self._scale_factor: float = scale or 1

        self.setZValue(self.Z_VALUE)
        self.set_parameters()

    @classmethod
    def create_from_json(cls, data: Dict[str, Any]) -> "PointComponent":
        """
        :param data: a dictionary with basic attributes that can be used to create an object.
        :return: class instance.
        """

        pen = ut.create_cosmetic_pen(QColor(data["pen_color"]), data["pen_width"])
        brush = QBrush(QColor(data["brush_color"]), data["brush_style"])
        component = PointComponent(data["radius"], pen, brush, increase_factor=data["increase_factor"],
                                   draggable=data["draggable"], selectable=data["selectable"],
                                   unique_selection=data["unique_selection"])
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
                "increase_factor": self._increase_factor,
                "radius": self._r}

    def copy(self) -> Tuple["PointComponent", QPointF]:
        """
        :return: copied component and its current position.
        """

        component = PointComponent(self._r, QPen(self._pen), QBrush(self._brush), self._scale_factor,
                                   self._increase_factor, self._draggable, self._selectable, self._unique_selection)
        return component, self.scenePos()

    def handle_selection(self, selected: bool = True) -> None:
        """
        :param selected: if selected is True and this item is selectable, this item is selected; otherwise, it is
        unselected.
        """

        self._set_rect(self._r * self._increase_factor if selected else self._r)

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

    def set_parameters(self, radius: Optional[float] = None, pen: Optional[QPen] = None, brush: Optional[QBrush] = None,
                       increase_factor: Optional[float] = None) -> None:
        """
        :param radius: point radius;
        :param pen: pen for component;
        :param brush: brush for component;
        :param increase_factor: point radius increase factor when selecting a point.
        """

        self._brush = brush or self._brush
        self._increase_factor = increase_factor or self._increase_factor
        self._pen = pen or self._pen
        self._r = radius or self._r

        self.setBrush(QBrush() if self._editable else self._brush)
        self.setPen(self._pen_to_edit if self._editable else self._pen)
        self._set_rect(self._r)

    def update_scale(self, scale_factor: float) -> None:
        """
        :param scale_factor: new scale factor.
        """

        super().update_scale(scale_factor)
        self._set_rect(self._r * self._increase_factor if self._r is not None and self.is_selected() else self._r)
