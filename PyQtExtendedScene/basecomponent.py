from typing import Any
from PyQt5.QtCore import QPointF
from PyQt5.QtWidgets import QGraphicsItem
from .sender import get_signal_sender


class BaseComponent:
    """
    Base class for scene component classes. Contains general attributes. Should be used as a parent class paired with
    some QGraphicsItem class.
    For example:

    class Rectangle(QGraphicsRectItem, BaseComponent):
        ...

    class Point(QGraphicsEllipseItem, BaseComponent):
        ...
    """

    def __init__(self, draggable: bool = True, selectable: bool = True, unique_selection: bool = False) -> None:
        """
        :param draggable: True if component can be dragged;
        :param selectable: True if component can be selected;
        :param unique_selection: True if selecting this component should reset all others selections
        ('selectable' must be set).
        """

        super().__init__()
        self._draggable: bool = draggable
        self._selectable: bool = selectable
        self._selected_at_group: bool = False
        self._selection_signal = get_signal_sender(bool)()
        self._selection_signal.connect(self.handle_selection)
        self._unique_selection: bool = unique_selection

        self._set_flags()

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

    def _set_flags(self) -> None:
        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.ItemIsMovable, self._draggable)
        self.setFlag(QGraphicsItem.ItemIsSelectable, self._selectable)

    def handle_selection(self, selected: bool = True) -> None:
        """
        :param selected: if selected is True and this item is selectable, this item is selected; otherwise, it is
        unselected.
        """

        ...

    def is_selected(self) -> bool:
        """
        :return: True if the component is selected (by itself or within a group).
        """

        return self._selected_at_group if self.parentItem() else self.isSelected()

    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value) -> Any:
        """
        :param change: the parameter of the item that is changing;
        :param value: the new value, the type of the value depends on change.
        """

        if change == QGraphicsItem.GraphicsItemChange.ItemSelectedChange:
            self._selection_signal.emit(value)

        for item_class in self.__class__.__bases__:
            if item_class != BaseComponent:
                return item_class().itemChange(change, value)

    def set_position_after_paste(self, mouse_pos: QPointF, item_pos: QPointF, left: float, top: float) -> None:
        """
        :param mouse_pos: mouse position;
        :param item_pos: position of the component when copying;
        :param left: x coordinate in the scene reference system that should be at the mouse position;
        :param top: y coordinate in the scene reference system that should be at the mouse position.
        """

        new_item_x = mouse_pos.x() + item_pos.x() - left
        new_item_y = mouse_pos.y() + item_pos.y() - top
        self.setPos(new_item_x, new_item_y)

    def set_selected_at_group(self, selected: bool) -> None:
        """
        :param selected: True if the component is selected within a group.
        """

        self._selected_at_group = selected
        self._selection_signal.emit(selected)

    def update_scale(self, scale_factor: float) -> None:
        """
        :param scale_factor: new scale factor.
        """

        ...
