from PyQt5.QtWidgets import QGraphicsItem, QGraphicsItemGroup
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
        :param item:
        """

        if hasattr(item, "update_scale"):
            self._scale_changed.connect(item.update_scale)

        super().addToGroup(item)

    def update_scale(self, scale_factor: float) -> None:
        """
        :param scale_factor: new scale factor.
        """

        self._scale_changed.emit(scale_factor)
