from typing import Any, Dict, Optional
from PyQt5.QtCore import QPointF
from PyQt5.QtGui import QBrush, QColor, QPen
from PyQt5.QtWidgets import QGraphicsItem
from . import utils as ut
from .scenemode import SceneMode
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

    PEN_COLOR: QColor = QColor("#0047AB")
    PEN_WIDTH: float = 2

    def __init__(self, pen: Optional[QPen] = None, brush: Optional[QBrush] = None, draggable: bool = True,
                 selectable: bool = True, unique_selection: bool = False) -> None:
        """
        :param pen: pen for component;
        :param brush: brush for component;
        :param draggable: True if component can be dragged in common mode;
        :param selectable: True if component can be selected in common mode;
        :param unique_selection: True if selecting this component should reset all others selections in common mode
        ('selectable' must be set).
        """

        super().__init__()
        self._brush: QBrush = brush or QBrush()
        self._drag_allowed: bool = True
        self._draggable: bool = draggable
        self._editable: bool = False
        self._pen: QPen = pen or ut.create_cosmetic_pen(self.PEN_COLOR, self.PEN_WIDTH)
        self._pen_to_edit: QPen = QPen(self._pen)
        self._scale_factor: float = 1
        self._scene_mode: SceneMode = SceneMode.NORMAL
        self._selectable: bool = selectable
        self._selected_at_group: bool = False
        self._unique_selection: bool = unique_selection

        self._create_selection_signal()
        self._set_flags()

    @classmethod
    def create_from_json(cls, data: Dict[str, Any]) -> Optional["BaseComponent"]:
        """
        :param data: a dictionary with basic attributes that can be used to create an object.
        :return: class instance.
        """

        return None

    @property
    def draggable(self) -> bool:
        """
        :return: True if component can be dragged in common mode.
        """

        return self._draggable

    @property
    def selectable(self) -> bool:
        """
        :return: True if component can be selected in common mode.
        """

        return self._selectable

    @property
    def unique_selection(self) -> bool:
        """
        :return: True if selecting this component should reset all others selections in common mode.
        """

        return self._unique_selection

    def _change_component_draggability_according_scene_flag(self) -> None:
        draggable = self._draggable if self._drag_allowed else False
        self.setFlag(QGraphicsItem.ItemIsMovable, draggable)

    def _create_selection_signal(self) -> None:
        self.selection_signal = get_signal_sender(bool)()
        self.selection_signal.component = self
        self.selection_signal.connect(self.handle_selection)

    def _set_flags(self) -> None:
        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.ItemIsMovable, self._draggable)
        self.setFlag(QGraphicsItem.ItemIsSelectable, self._selectable)

    def allow_drag(self, allow: bool) -> None:
        """
        :param allow: if True, then components are allowed to be moved around the scene.
        """

        self._drag_allowed = allow
        self._change_component_draggability_according_scene_flag()

    def convert_to_json(self) -> Dict[str, Any]:
        """
        :return: dictionary with basic object attributes.
        """

        return {"brush_color": self._brush.color().rgba(),
                "brush_style": self._brush.style(),
                "class": self.__class__.__name__,
                "draggable": self._draggable,
                "pen_color": self._pen.color().rgba(),
                "pen_width": self._pen.widthF(),
                "selectable": self._selectable,
                "unique_selection": self._unique_selection,
                "pos": (self.scenePos().x(), self.scenePos().y())}

    def handle_selection(self, selected: bool = True) -> None:
        """
        :param selected: if selected is True and this item is selectable, this item is selected; otherwise, it is
        unselected.
        """

        ...

    def is_in_group(self) -> bool:
        """
        :return: True if the item belongs to the component group.
        """

        from .componentgroup import ComponentGroup

        return isinstance(self.parentItem(), ComponentGroup)

    def is_selected(self) -> bool:
        """
        :return: True if the component is selected (by itself or within a group).
        """

        return self._selected_at_group if self.is_in_group() else self.isSelected()

    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value) -> Any:
        """
        :param change: the parameter of the item that is changing;
        :param value: the new value, the type of the value depends on change.
        """

        if change == QGraphicsItem.ItemSelectedChange:
            self.selection_signal.emit(value)

        for item_class in self.__class__.__bases__:
            if item_class != BaseComponent:
                return item_class().itemChange(change, value)

    def set_editable(self, editable: bool, pen: Optional[QPen] = None) -> None:
        """
        :param editable: if True, then the component can be edited;
        :param pen: pen to be used to draw the component when editing.
        """

        self._editable = editable
        self._pen_to_edit = pen or self._pen_to_edit

        if hasattr(self, "setPen"):
            self.setPen(self._pen_to_edit if self._editable else self._pen)

        if hasattr(self, "setBrush"):
            self.setBrush(QBrush() if self._editable else self._brush)

    def set_position_after_paste(self, mouse_pos: QPointF, item_pos: QPointF, left_top: QPointF) -> None:
        """
        :param mouse_pos: mouse position;
        :param item_pos: position of the component when copying;
        :param left_top: x and y coordinates in the scene reference system that should be at the mouse position.
        """

        self.setPos(mouse_pos + item_pos - left_top)

    def set_scene_mode(self, mode: SceneMode) -> None:
        """
        :param mode: new scene mode.
        """

        self._scene_mode = mode
        if self._scene_mode == SceneMode.NORMAL:
            self._change_component_draggability_according_scene_flag()
            self.setFlag(QGraphicsItem.ItemIsSelectable, self._selectable)
        elif self._scene_mode == SceneMode.EDIT and not self.is_in_group():
            self.setFlag(QGraphicsItem.ItemIsMovable, True)
            self.setFlag(QGraphicsItem.ItemIsSelectable, True)

    def set_selected_at_group(self, selected: bool) -> None:
        """
        :param selected: True if the component is selected within a group.
        """

        self._selected_at_group = selected
        self.selection_signal.emit(selected)

    def update_scale(self, scale_factor: float) -> None:
        """
        :param scale_factor: new scale factor.
        """

        self._scale_factor = scale_factor
