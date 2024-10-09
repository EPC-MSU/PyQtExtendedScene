from enum import auto, Enum
from typing import List, Optional, Tuple
from PyQt5.QtCore import pyqtSignal, QPoint, QPointF, QRectF, Qt, QTimer
from PyQt5.QtGui import QBrush, QColor, QKeyEvent, QKeySequence, QMouseEvent, QPixmap, QWheelEvent
from PyQt5.QtWidgets import QFrame, QGraphicsItem, QGraphicsPixmapItem, QGraphicsScene, QGraphicsView, QShortcut
from . import utils as ut
from .abstractcomponent import AbstractComponent
from .basecomponent import BaseComponent
from .componentgroup import ComponentGroup
from .pointcomponent import PointComponent
from .scalablecomponent import ScalableComponent
from .scenemode import SceneMode


class ExtendedScene(QGraphicsView):
    """
    Widget for working with graphic objects.
    """

    MIN_SCALE: float = 0.1
    UPDATE_INTERVAL: int = 10  # msec
    _edited_group_component_signal: pyqtSignal = pyqtSignal(QGraphicsItem)
    left_clicked: pyqtSignal = pyqtSignal(QPointF)
    middle_clicked: pyqtSignal = pyqtSignal(QPointF)
    on_component_left_click: pyqtSignal = pyqtSignal(QGraphicsItem)
    on_component_right_click: pyqtSignal = pyqtSignal(QGraphicsItem)
    on_component_moved: pyqtSignal = pyqtSignal(QGraphicsItem)
    right_clicked: pyqtSignal = pyqtSignal(QPointF)
    scale_changed: pyqtSignal = pyqtSignal(float)
    scene_mode_changed: pyqtSignal = pyqtSignal(SceneMode)

    class Operation(Enum):
        """
        Enumerating possible widget operations.
        """

        CREATE_COMPONENT = auto()
        DRAG = auto()
        DRAG_COMPONENT = auto()
        NO_ACTION = auto()
        RESIZE_COMPONENT = auto()
        SELECT_COMPONENT = auto()

    def __init__(self, background: Optional[QPixmap] = None, zoom_speed: float = 0.001, parent=None) -> None:
        """
        :param background: pixmap background for scene;
        :param zoom_speed: zoom speed;
        :param parent: parent.
        """

        super().__init__(parent)
        self._components: List[QGraphicsItem] = []
        self._components_in_operation: List[QGraphicsItem] = []
        self._copied_components: List[Tuple[BaseComponent, QPointF]] = []
        self._current_component: Optional[QGraphicsItem] = None
        self._drag_allowed: bool = True
        self._group: Optional[ComponentGroup] = None
        self._mode: SceneMode = SceneMode.NO_ACTION
        self._mouse_pos: QPointF = QPointF()
        self._operation: ExtendedScene.Operation = ExtendedScene.Operation.NO_ACTION
        self._scale: float = 1.0
        self._shift_pressed: bool = False
        self._zoom_speed: float = zoom_speed

        self._scene: QGraphicsScene = QGraphicsScene()
        self.setScene(self._scene)
        self._background: Optional[QGraphicsPixmapItem] = self._scene.addPixmap(background) if background else None

        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setBackgroundBrush(QBrush(QColor(0, 0, 0)))
        self.setFrameShape(QFrame.NoFrame)
        self.setMouseTracking(True)
        # For keyboard events
        self.setFocusPolicy(Qt.StrongFocus)

        self._animation_timer: QTimer = QTimer()
        self._animation_timer.start(ExtendedScene.UPDATE_INTERVAL)
        self._copy_shortcut: QShortcut = QShortcut(QKeySequence(Qt.CTRL + Qt.Key_C), self)
        self._copy_shortcut.setContext(Qt.WindowShortcut)
        self._copy_shortcut.activated.connect(self.copy_selected_components)
        self._delete_shortcut: QShortcut = QShortcut(QKeySequence(Qt.Key_Delete), self)
        self._delete_shortcut.setContext(Qt.WindowShortcut)
        self._delete_shortcut.activated.connect(self.delete_selected_components)
        self._paste_shortcut: QShortcut = QShortcut(QKeySequence(Qt.CTRL + Qt.Key_V), self)
        self._paste_shortcut.setContext(Qt.WindowShortcut)
        self._paste_shortcut.activated.connect(self.paste_copied_components)

    def _add_items_to_edited_group(self) -> None:
        group = self._group or ComponentGroup()

        for item in self._components_in_operation:
            self.remove_component(item)
            item.setFlag(QGraphicsItem.ItemIsMovable, item.draggable)
            item.setFlag(QGraphicsItem.ItemIsSelectable, item.selectable)
            group.addToGroup(item)

        if not self._components_in_operation:
            if self._group:
                self._scene.removeItem(self._group)
        else:
            if not self._group:
                self.add_component(group)
            else:
                self._group.show()
            self._edited_group_component_signal.emit(group)

        self._group = None
        self._components_in_operation.clear()

    def _finish_create_point_component_by_mouse(self) -> None:
        self._current_component.setSelected(False)
        self._scene.removeItem(self._current_component)
        self.add_component(self._current_component)
        self._components_in_operation.append(self._current_component)
        self._current_component = None
        self._operation = ExtendedScene.Operation.NO_ACTION

    def _finish_create_scalable_component_by_mouse(self) -> None:
        self._scene.removeItem(self._current_component)
        if self._current_component.check_big_enough():
            self._current_component.fix_mode(ScalableComponent.Mode.NO_ACTION)
            self.add_component(self._current_component)
            self._components_in_operation.append(self._current_component)
        self._current_component = None
        self._operation = ExtendedScene.Operation.NO_ACTION

    def _get_clicked_item(self, event: QMouseEvent) -> Optional[QGraphicsItem]:
        """
        :param event: mouse event.
        :return: a component that is located at the point specified by the mouse.
        """

        for item in self.items(event.pos()):
            if isinstance(item, (AbstractComponent, BaseComponent)):
                return item.group() if item.group() else item

        return None

    def _handle_component_creation_by_mouse(self) -> None:
        if isinstance(self._current_component, PointComponent):
            self._current_component.setPos(self._mouse_pos)
        elif isinstance(self._current_component, ScalableComponent):
            self._current_component.resize_by_mouse(self._mouse_pos)

    def _handle_component_resize_by_mouse(self) -> None:
        self._current_component.resize_by_mouse(self._mouse_pos)

    def _handle_mouse_left_button_press(self, item: Optional[QGraphicsItem], pos: QPointF) -> None:
        """
        :param item: component clicked by mouse;
        :param pos: mouse position.
        """

        if item:
            self.on_component_left_click.emit(item)
        else:
            self.left_clicked.emit(pos)

        if self._mode in (SceneMode.EDIT, SceneMode.EDIT_GROUP) and item in self._components_in_operation:
            if item and self._set_resize_mode_for_scalable_component(item):
                return

            if item:
                self._set_drag_component_mode(item)
                return

        if item:
            return

        # We are in drag board mode now
        self.remove_all_selections()
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self._operation = ExtendedScene.Operation.DRAG

    def _handle_mouse_left_button_release(self) -> None:
        if self._operation is ExtendedScene.Operation.DRAG_COMPONENT:
            if self._scene.selectedItems():
                for item in self._scene.selectedItems():
                    self.on_component_moved.emit(item)
        elif self._operation is ExtendedScene.Operation.RESIZE_COMPONENT:
            self._current_component.setFlag(QGraphicsItem.ItemIsMovable, True)
            self._current_component = None

        self.setDragMode(QGraphicsView.NoDrag)
        self._operation = ExtendedScene.Operation.NO_ACTION

    def _handle_mouse_middle_button_press(self, pos: QPointF) -> None:
        """
        :param pos: mouse position.
        """

        self.middle_clicked.emit(pos)

    def _handle_mouse_right_button_press(self, item: QGraphicsItem, pos: QPointF) -> None:
        """
        :param item: component clicked by mouse;
        :param pos: mouse position.
        """

        if item:
            self.on_component_right_click.emit(item)
        else:
            self.right_clicked.emit(pos)

        if self._mode is SceneMode.NO_ACTION:
            self._set_select_component_mode()
        elif self._mode in (SceneMode.EDIT, SceneMode.EDIT_GROUP):
            if self._shift_pressed:
                self._start_create_point_component_by_mouse(pos)
            else:
                self._start_create_scalable_component_by_mouse(pos)

    def _handle_mouse_right_button_release(self) -> None:
        if self._mode is SceneMode.NO_ACTION:
            self._set_no_action_mode()
        elif self._mode in (SceneMode.EDIT, SceneMode.EDIT_GROUP):
            if isinstance(self._current_component, PointComponent):
                self._finish_create_point_component_by_mouse()
            elif isinstance(self._current_component, ScalableComponent):
                self._finish_create_scalable_component_by_mouse()

    def _remove_items_from_edited_group(self) -> None:
        self._components_in_operation = []
        items = self._scene.selectedItems()
        self._group = items[0] if len(items) == 1 and isinstance(items[0], ComponentGroup) else None

        for component in self._components:
            if component is not self._group:
                component.setFlag(QGraphicsItem.ItemIsMovable, False)
                component.setFlag(QGraphicsItem.ItemIsSelectable, False)

        if self._group:
            for child_item in self._group.set_edit_group_mode():
                self.add_component(child_item)
                self._components_in_operation.append(child_item)
                child_item.setFlag(QGraphicsItem.ItemIsMovable, True)
                child_item.setFlag(QGraphicsItem.ItemIsSelectable, True)

            self._group.hide()

    def _set_drag_component_mode(self, item: QGraphicsItem) -> None:
        """
        :param item: component that will be dragged.
        """

        self.remove_all_selections()
        item.setSelected(True)
        self._operation = ExtendedScene.Operation.DRAG_COMPONENT

    def _set_no_action_mode(self) -> None:
        self.setDragMode(QGraphicsView.NoDrag)
        self._operation = ExtendedScene.Operation.NO_ACTION

    def _set_resize_mode_for_scalable_component(self, item: ScalableComponent) -> bool:
        """
        :param item: component that will be resized.
        :return: True if the mode is set.
        """

        if (isinstance(item, ScalableComponent) and item.isSelected() and not item.is_in_group() and
                item.mode not in (ScalableComponent.Mode.MOVE, ScalableComponent.Mode.NO_ACTION)):
            item.go_to_resize_mode()
            self._current_component = item
            self._operation = ExtendedScene.Operation.RESIZE_COMPONENT
            return True

        return False

    def _set_select_component_mode(self) -> None:
        self.setDragMode(QGraphicsView.RubberBandDrag)
        self._operation = ExtendedScene.Operation.SELECT_COMPONENT

    def _start_create_point_component_by_mouse(self, pos: QPointF) -> None:
        """
        :param pos: mouse position.
        """

        if self._current_component:
            self._scene.removeItem(self._current_component)

        self._current_component = PointComponent(scale=self._scale)
        self._current_component.setPos(pos)
        self._scene.addItem(self._current_component)
        self._operation = ExtendedScene.Operation.CREATE_COMPONENT

    def _start_create_scalable_component_by_mouse(self, pos: QPointF) -> None:
        """
        :param pos: mouse position.
        """

        if self._current_component:
            self._scene.removeItem(self._current_component)

        self._current_component = ScalableComponent(QRectF(QPointF(0, 0), QPointF(0, 0)))
        self._current_component.setPos(pos)
        self._scene.addItem(self._current_component)
        self._current_component.fix_mode(ScalableComponent.Mode.RESIZE_ANY)
        self._operation = ExtendedScene.Operation.CREATE_COMPONENT

    def add_component(self, component: QGraphicsItem) -> None:
        """
        :param component: component to be added to the scene.
        """

        self._components.append(component)
        self._scene.addItem(component)
        component.update_scale(self._scale)
        self.scale_changed.connect(component.update_scale)
        component.set_scene_mode(self._mode)
        self.scene_mode_changed.connect(component.set_scene_mode)
        if isinstance(component, ScalableComponent):
            self._animation_timer.timeout.connect(component.update_selection)
        elif isinstance(component, ComponentGroup):
            component.set_animation_timer(self._animation_timer)

    def all_components(self, class_filter: type = object) -> List[QGraphicsItem]:
        """
        :param class_filter: filter for components on scene.
        :return: list of components that match a given filter.
        """

        return list(filter(lambda x: isinstance(x, class_filter), self._components))

    def allow_drag(self, allow: bool = True) -> None:
        """
        :param allow: if True, then components are allowed to be moved around the scene.
        """

        self._drag_allowed = allow

    def clear_scene(self) -> None:
        self._scene.clear()
        self._components = []
        self._background = None
        self.resetTransform()

    def copy_selected_components(self) -> None:
        self._copied_components = [item.copy() for item in self._scene.selectedItems()
                                   if isinstance(item, BaseComponent)]

    def delete_selected_components(self) -> None:
        if self._mode is SceneMode.NO_ACTION:
            return

        for item in self._scene.selectedItems():
            self.remove_component(item)
            try:
                self._components_in_operation.remove(item)
            except ValueError:
                pass

    def is_drag_allowed(self) -> bool:
        """
        :return: if True, then components are allowed to be moved around the scene.
        """

        return self._drag_allowed

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """
        :param event: key event.
        """

        if event.key() == Qt.Key_Shift and self._mode is not SceneMode.NO_ACTION:
            self._shift_pressed = True

    def keyReleaseEvent(self, event: QKeyEvent) -> None:
        """
        :param event: key event.
        """

        if event.key() == Qt.Key_Shift and self._mode is not SceneMode.NO_ACTION:
            self._shift_pressed = False

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """
        :param event: mouse event.
        """

        self._mouse_pos = self.mapToScene(event.pos())
        if self._operation is ExtendedScene.Operation.CREATE_COMPONENT:
            self._handle_component_creation_by_mouse()
            return

        if self._operation is ExtendedScene.Operation.RESIZE_COMPONENT:
            self._handle_component_resize_by_mouse()

        super().mouseMoveEvent(event)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """
        :param event: mouse event.
        """

        item = self._get_clicked_item(event)
        pos = self.mapToScene(event.pos())
        if event.button() == Qt.LeftButton:
            self._handle_mouse_left_button_press(item, pos)
        elif event.button() == Qt.MiddleButton:
            self._handle_mouse_middle_button_press(pos)
        elif event.button() == Qt.RightButton:
            self._handle_mouse_right_button_press(item, pos)

        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """
        :param event: mouse event.
        """

        if event.button() == Qt.LeftButton:
            self._handle_mouse_left_button_release()
        elif event.button() == Qt.RightButton:
            self._handle_mouse_right_button_release()

        super().mouseReleaseEvent(event)

    def paste_copied_components(self) -> None:
        if self._mode is not SceneMode.EDIT:
            return

        self.remove_all_selections()
        left, top = ut.get_left_top_pos([pos for _, pos in self._copied_components])

        for item, item_pos in self._copied_components:
            item_to_paste = item.copy()[0]
            item_to_paste.set_position_after_paste(self._mouse_pos, item_pos, left, top)
            self.add_component(item_to_paste)
            item_to_paste.setSelected(True)

    def remove_all_selections(self, components: Optional[List[QGraphicsItem]] = None) -> None:
        components = components or self._components
        for item in components:
            item.setSelected(False)

    def remove_component(self, component: QGraphicsItem) -> None:
        """
        :param component: component to be removed from the scene.
        """

        self._components.remove(component)
        self._scene.removeItem(component)
        self.scale_changed.disconnect(component.update_scale)
        self.scene_mode_changed.disconnect(component.set_scene_mode)
        if isinstance(component, ScalableComponent):
            self._animation_timer.timeout.disconnect(component.update_selection)

    def scale_to_window_size(self, x: float, y: float) -> None:
        """
        Scale to window size.
        For example, if you have window 600x600 and workspace background image 1200x1200, image will be scaled in 4x.
        :param x: window width;
        :param y: window height.
        """

        factor_x = x / self._background.pixmap().width()
        factor_y = y / self._background.pixmap().height()
        factor = max(min(factor_x, factor_y), self.MIN_SCALE)
        self.resetTransform()
        self._scale = factor
        self.zoom(factor, QPoint(0, 0))

    def set_background(self, background: QPixmap) -> None:
        """
        :param background: new pixmap background for scene.
        """

        if self._background:
            raise ValueError("Call 'clear_scene' first!")

        self._background = self._scene.addPixmap(background)

    def set_scene_mode(self, mode: SceneMode) -> None:
        """
        :param mode: new scene mode.
        """

        if self._mode is SceneMode.EDIT_GROUP:
            self._add_items_to_edited_group()

        self._mode = mode
        self.scene_mode_changed.emit(mode)

        if mode is SceneMode.EDIT:
            self._components_in_operation = self._components[:]
        elif mode is SceneMode.EDIT_GROUP:
            self._remove_items_from_edited_group()
        else:
            self._components_in_operation = []

    def wheelEvent(self, event: QWheelEvent) -> None:
        """
        :param event: wheel event.
        """

        zoom_factor = 1.0
        zoom_factor += event.angleDelta().y() * self._zoom_speed
        if self._scale * zoom_factor < self.MIN_SCALE and zoom_factor < 1.0:  # minimum allowed zoom
            return

        self.zoom(zoom_factor, event.pos())
        self._scale *= zoom_factor
        self.scale_changed.emit(self._scale)

    def zoom(self, zoom_factor: float, pos: QPoint) -> None:  # pos in view coordinates
        """
        :param zoom_factor: scale factor;
        :param pos:
        """

        old_scene_pos = self.mapToScene(pos)

        # Note: Workaround! See:
        # - https://bugreports.qt.io/browse/QTBUG-7328
        # - https://stackoverflow.com/questions/14610568/how-to-use-the-qgraphicsviews-translate-function
        anchor = self.transformationAnchor()
        self.setTransformationAnchor(QGraphicsView.NoAnchor)  # Override transformation anchor
        self.scale(zoom_factor, zoom_factor)
        delta = self.mapToScene(pos) - old_scene_pos
        self.translate(delta.x(), delta.y())
        self.setTransformationAnchor(anchor)  # Restore old anchor
