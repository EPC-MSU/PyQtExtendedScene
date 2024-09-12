from PyQt5.QtCore import pyqtSignal, QObject, QRectF
from PyQt5.QtGui import QPainter
from PyQt5.QtWidgets import QGraphicsItem, QStyleOptionGraphicsItem, QWidget


class Sender(QObject):

    signal: pyqtSignal = pyqtSignal(bool)

    def connect(self, func) -> None:
        self.signal.connect(func)

    def emit(self, value: bool) -> None:
        self.signal.emit(value)


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
        self._selection_signal: Sender = Sender()
        self._selection_signal.connect(self.handle_selection)
        self._unique_selection: bool = unique_selection

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

    def boundingRect(self) -> QRectF:
        """
        :return: the outer bounds of the component as a rectangle.
        """

        # By default, bounding rect of our object is a bounding rect of children items
        return self.childrenBoundingRect()

    def handle_selection(self, selected: bool = True) -> None:
        """
        :param selected: if True, then set the component as selected.
        """

        ...

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

        ...

    def update_scale(self, scale_factor: float) -> None:
        """
        :param scale_factor: new scale factor.
        """

        ...
