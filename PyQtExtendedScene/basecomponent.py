from typing import Any
from PyQt5.QtWidgets import QGraphicsItem
from .sender import get_signal_sender


class BaseComponent:

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

    @staticmethod
    def update_scale(scale_factor: float) -> None:
        """
        :param scale_factor: new scale factor.
        """

        ...
