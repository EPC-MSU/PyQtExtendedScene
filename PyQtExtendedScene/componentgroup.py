import logging
from typing import Any, Dict, Generator, Optional, Tuple
from PyQt5.QtCore import QPointF, QRectF, Qt, QTimer
from PyQt5.QtWidgets import (QGraphicsItem, QGraphicsItemGroup, QGraphicsPixmapItem, QGraphicsSceneHoverEvent,
                             QGraphicsSceneMouseEvent)
from . import utils as ut
from .basecomponent import BaseComponent
from .pointcomponent import PointComponent
from .rectcomponent import RectComponent
from .scenemode import SceneMode
from .sender import get_signal_sender


logger = logging.getLogger("pyqtextendedscene")


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
        BaseComponent.__init__(self, draggable=draggable, selectable=selectable, unique_selection=unique_selection)

        self._animation_timer: Optional[QTimer] = None
        self._scale_changed = get_signal_sender(float)()
        self._scene_mode_changed = get_signal_sender(SceneMode)()

    @classmethod
    def create_from_json(cls, data: Dict[str, Any]) -> "ComponentGroup":
        """
        :param data: a dictionary with basic attributes that can be used to create an object.
        :return: class instance.
        """

        group = ComponentGroup(data["draggable"], data["selectable"], data["unique_selection"])
        for component_data in data["components"]:
            component_class = ut.get_class_by_name(component_data["class"])
            if not component_class or not hasattr(component_class, "create_from_json"):
                continue

            component = component_class.create_from_json(component_data)
            if not component:
                continue

            component.setPos(QPointF(*component_data["pos"]))
            group.addToGroup(component)
        return group

    def _remove_child_from_group_and_scene(self, component: QGraphicsItem) -> None:
        """
        :param component: child component to be removed from the group and scene.
        """

        self.removeFromGroup(component)
        if self.scene():
            self.scene().removeItem(component)
        logging.debug("%s removed from group %s", component, self)

    def addToGroup(self, component: QGraphicsItem) -> None:
        """
        :param component: component to be added to the group.
        """

        if isinstance(component, BaseComponent):
            self._scale_changed.connect(component.update_scale)
            self._scene_mode_changed.connect(component.set_scene_mode)

        if self._animation_timer and isinstance(component, RectComponent):
            self._animation_timer.timeout.connect(component.update_selection)

        super().addToGroup(component)

    def copy(self) -> Tuple["ComponentGroup", QPointF]:
        """
        :return: copied component and its current position.
        """

        component = ComponentGroup(self._draggable, self._selectable, self._unique_selection)
        points = []
        for component in self.childItems():
            if hasattr(component, "copy"):
                copied_component, pos = component.copy()
                copied_component.setPos(pos)
                component.addToGroup(copied_component)
                points.append(pos)
        return component, ut.get_left_top_pos(points)

    def convert_to_json(self) -> Dict[str, Any]:
        """
        :return: dictionary with basic object attributes.
        """

        components_data = []
        points = []
        for component in self.childItems():
            if isinstance(component, BaseComponent):
                component_data = component.convert_to_json()
                components_data.append(component_data)
                points.append(QPointF(*component_data["pos"]))

        pos = ut.get_left_top_pos(points)
        return {**super().convert_to_json(),
                "components": components_data,
                "pos": (pos.x(), pos.y())}

    def get_top_left_and_bottom_right_points(self) -> Tuple[QPointF, QPointF]:
        """
        :return: points at the top left and bottom right vertices of the rectangle bounding the group component.
        """

        rect = ut.get_min_rect_for_components(self.childItems())
        return rect.topLeft(), rect.bottomRight()

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

    def limit_size_to_background(self, background: Optional[QGraphicsPixmapItem]) -> None:
        """
        :param background: background of scene.
        """

        if not background:
            return

        background_rect = background.sceneBoundingRect()
        for child_item in self.childItems():
            if isinstance(child_item, PointComponent) and not background.contains(self.mapToScene(child_item.pos())):
                self._remove_child_from_group_and_scene(child_item)
            elif isinstance(child_item, RectComponent):
                rect = child_item.mapRectToScene(child_item.rect())
                modified_rect = ut.fit_rect_to_background(background_rect, rect)
                if modified_rect == rect:
                    continue

                self._remove_child_from_group_and_scene(child_item)
                if modified_rect:
                    child_item.setRect(QRectF(QPointF(0, 0), modified_rect.size()))
                    child_item.setPos(modified_rect.topLeft())
                    self.addToGroup(child_item)

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

    def rotate_clockwise(self, angle: float, center: QPointF) -> None:
        """
        :param angle: the angle in degrees by which the item should be rotated clockwise;
        :param center: the point around which the item needs to be rotated.
        """

        for item in self.childItems():
            if not hasattr(item, "rotate_clockwise"):
                return

        child_items = self.childItems()
        for item in child_items:
            self.removeFromGroup(item)

        for item in child_items:
            item.rotate_clockwise(angle, center)
            self.addToGroup(item)

    def set_animation_timer(self, timer: QTimer) -> None:
        """
        :param timer: new timer for animation.
        """

        for item in self.childItems():
            if isinstance(item, RectComponent):
                if self._animation_timer:
                    try:
                        self._animation_timer.disconnect(item.update_selection)
                    except TypeError:
                        pass

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

    def set_position_after_paste(self, mouse_pos: QPointF, item_pos: QPointF, left_top: QPointF) -> None:
        """
        :param mouse_pos: mouse position;
        :param item_pos: position of the component when copying;
        :param left_top: x and y coordinates in the scene reference system that should be at the mouse position.
        """

        self.prepareGeometryChange()
        items = []
        for item in self.childItems():
            item.setPos(mouse_pos + item.scenePos() - left_top)
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
