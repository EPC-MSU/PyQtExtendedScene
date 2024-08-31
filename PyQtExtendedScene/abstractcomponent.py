from PyQt5.QtCore import QRectF
from PyQt5.QtGui import QPainter
from PyQt5.QtWidgets import QGraphicsItem, QWidget


class AbstractComponent(QGraphicsItem):
    """
    Abstract component for extended scene.
    """

    def __init__(self, draggable: bool = True, selectable: bool = True, unique_selection: bool = True) -> None:
        """
        :param draggable: True if component can be dragged;
        :param selectable: True if component can be selected;
        :param unique_selection: True if selecting this component should reset all others selections
        ('selectable' must be set).
        """

        super().__init__()
        self._draggable: bool = draggable
        self._selectable: bool = selectable
        self._selected: bool = False
        self._unique_selection: bool = unique_selection

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
    def selected(self) -> bool:
        return self._selected

    @property
    def unique_selection(self) -> bool:
        """
        :return: True if selecting this component should reset all others selections.
        """

        return self._unique_selection

    def boundingRect(self) -> QRectF:
        """
        :return: the outer bounds of the component as a rectangle.
        """

        # By default, bounding rect of our object is a bounding rect of children items
        return self.childrenBoundingRect()

    def paint(self, painter: QPainter, option, widget: QWidget = None) -> None:
        """
        :param painter: painter;
        :param option: style options for the component, such as its state, exposed area and its level-of-detail hints;
        :param widget: widget argument is optional. If provided, it points to the widget that is being painted on;
        otherwise, it is None.
        """

        pass

    def select(self, selected: bool = True) -> None:
        """
        :param selected: if True, then set the component as selected.
        """

        if self._selectable:
            self._selected = selected

    def update_scale(self, scale: float) -> None:
        """
        :param scale: new scale factor for component.
        """

        pass
