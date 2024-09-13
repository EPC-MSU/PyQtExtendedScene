from typing import Tuple
from PyQt5.QtCore import QPointF
from PyQt5.QtWidgets import QGraphicsItem, QGraphicsItemGroup
from . import utils as ut
from .basecomponent import BaseComponent
from .sender import get_signal_sender


class ComponentGroup(QGraphicsItemGroup, BaseComponent):
    """
    Class for combining components into a group.
    """

    def __init__(self, draggable: bool = True, selectable: bool = True, unique_selection: bool = False) -> None:
        """
        :param draggable: True if component can be dragged;
        :param selectable: True if component can be selected;
        :param unique_selection: True if selecting this component should reset all others selections
        ('selectable' must be set).
        """

        QGraphicsItemGroup.__init__(self)
        BaseComponent.__init__(self, draggable, selectable, unique_selection)

        self._scale_changed = get_signal_sender(float)()

    def addToGroup(self, item: QGraphicsItem) -> None:
        """
        :param item: item to be added to the group.
        """

        if hasattr(item, "update_scale"):
            self._scale_changed.connect(item.update_scale)

        super().addToGroup(item)

    def copy(self) -> Tuple["ComponentGroup", QPointF]:
        """
        :return: copied component and its current position.
        """

        component = ComponentGroup(self._draggable, self._selectable, self._unique_selection)
        points = []
        for item in self.childItems():
            if hasattr(item, "copy"):
                copied_item, pos = item.copy()
                copied_item.setPos(pos)
                component.addToGroup(copied_item)
                points.append(pos)
        return component, QPointF(*ut.get_left_top_pos(points))

    def set_position_after_paste(self, mouse_pos: QPointF, item_pos: QPointF, left: float, top: float) -> None:
        """
        :param mouse_pos: mouse position;
        :param item_pos: position of the component when copying;
        :param left: x coordinate in the scene reference system that should be at the mouse position;
        :param top: y coordinate in the scene reference system that should be at the mouse position.
        """

        self.prepareGeometryChange()
        items = []
        for item in self.childItems():
            new_item_x = mouse_pos.x() + item.scenePos().x() - left
            new_item_y = mouse_pos.y() + item.scenePos().y() - top
            item.setPos(new_item_x, new_item_y)
            items.append(item)

        for item in items:
            self.removeFromGroup(item)
            self.addToGroup(item)

    def update_scale(self, scale_factor: float) -> None:
        """
        :param scale_factor: new scale factor.
        """

        self._scale_changed.emit(scale_factor)
