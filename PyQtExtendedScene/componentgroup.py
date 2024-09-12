from PyQt5.QtWidgets import QGraphicsItem, QGraphicsItemGroup


class ComponentGroup(QGraphicsItemGroup):
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

        super().__init__()
        self._draggable: bool = draggable
        self._selectable: bool = selectable
        self._unique_selection: bool = unique_selection

        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.ItemIsMovable, draggable)
        self.setFlag(QGraphicsItem.ItemIsSelectable, selectable)

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

    def update_scale(self, scale_factor: float) -> None:
        """
        :param scale_factor: new scale factor.
        """

        pass
