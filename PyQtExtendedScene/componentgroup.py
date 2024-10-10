from typing import Generator, Optional, Tuple
from PyQt5.QtCore import QPointF, Qt, QTimer
from PyQt5.QtWidgets import QGraphicsItem, QGraphicsItemGroup, QGraphicsSceneHoverEvent, QGraphicsSceneMouseEvent
from . import utils as ut
from .basecomponent import BaseComponent
from .rectcomponent import RectComponent
from .scenemode import SceneMode
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

        self._animation_timer: Optional[QTimer] = None
        self._scale_changed = get_signal_sender(float)()
        self._scene_mode_changed = get_signal_sender(SceneMode)()

    def addToGroup(self, item: QGraphicsItem) -> None:
        """
        :param item: item to be added to the group.
        """

        if hasattr(item, "update_scale"):
            self._scale_changed.connect(item.update_scale)

        if hasattr(item, "set_scene_mode"):
            self._scene_mode_changed.connect(item.set_scene_mode)

        if self._animation_timer and isinstance(item, RectComponent):
            self._animation_timer.timeout.connect(item.update_selection)

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

    def handle_selection(self, selected: bool = True) -> None:
        """
        :param selected: if selected is True and this item is selectable, this item is selected; otherwise, it is
        unselected.
        """

        if not selected:
            for item in self.childItems():
                item.set_selected_at_group(selected)

    def hoverEnterEvent(self, event: QGraphicsSceneHoverEvent) -> None:
        """
        :param event: hover event.
        """

        for item in self.childItems():
            if isinstance(item, RectComponent):
                item.hoverEnterEvent(event)

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        """
        :param event: mouse event.
        """

        if event.button() == Qt.LeftButton and self.flags() & QGraphicsItem.ItemIsSelectable:
            for item in self.childItems():
                if item.contains(self.mapToItem(item, event.pos())):
                    item.set_selected_at_group(True)
                elif item.is_selected():
                    item.set_selected_at_group(False)

    def set_animation_timer(self, timer: QTimer) -> None:
        """
        :param timer: new timer for animation.
        """

        for item in self.childItems():
            if isinstance(item, RectComponent):
                if self._animation_timer:
                    self._animation_timer.disconnect(item.update_selection)
                if timer is not None:
                    timer.timeout.connect(item.update_selection)

        self._animation_timer = timer

    def set_edit_group_mode(self) -> Generator[QGraphicsItem, None, None]:
        """
        :yield: components that are in a group.
        """

        for item in self.childItems():
            self.removeFromGroup(item)
            self.scene().removeItem(item)
            yield item

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

    def set_scene_mode(self, mode: SceneMode) -> None:
        """
        :param mode: new scene mode.
        """

        super().set_scene_mode(mode)
        self._scene_mode_changed.emit(mode)

    def update_scale(self, scale_factor: float) -> None:
        """
        :param scale_factor: new scale factor.
        """

        self._scale_changed.emit(scale_factor)
