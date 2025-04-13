import json
import logging
from enum import auto, Enum
from typing import Any, Dict, List, Optional
from PyQt5.QtCore import (pyqtSignal, pyqtSlot, QCoreApplication as qApp, QMimeData, QPoint, QPointF, QRect, QRectF,
                          QSize, QSizeF, Qt, QTimer)
from PyQt5.QtGui import (QBrush, QColor, QKeyEvent, QKeySequence, QMouseEvent, QPainter, QPainterPath, QPen, QPixmap,
                         QWheelEvent)
from PyQt5.QtWidgets import (QFrame, QGraphicsItem, QGraphicsPixmapItem, QGraphicsScene, QGraphicsView, QRubberBand,
                             QShortcut)
from . import utils as ut
from .basecomponent import BaseComponent
from .componentgroup import ComponentGroup
from .drawingmode import DrawingMode
from .pointcomponent import PointComponent
from .rectcomponent import RectComponent
from .rubberband import RubberBand
from .scenemode import SceneMode


logger = logging.getLogger("pyqtextendedscene")


class ExtendedScene(QGraphicsView):
    """
    Widget for working with graphic objects.
    """

    PEN_COLOR_TO_EDIT: QColor = QColor("#007FFF")
    PEN_WIDTH_TO_EDIT: float = 3
    MIME_TYPE: str = "PyQtExtendedScene_MIME"
    MIN_SCALE: float = 0.1
    POINT_INCREASE_FACTOR: float = 2
    POINT_RADIUS: float = 4
    UPDATE_INTERVAL_MS: int = 10  # msec
    component_deleted: pyqtSignal = pyqtSignal(QGraphicsItem)
    component_moved: pyqtSignal = pyqtSignal(QGraphicsItem)
    component_pasted: pyqtSignal = pyqtSignal(QGraphicsItem)
    custom_context_menu_requested: pyqtSignal = pyqtSignal(QPoint)
    edited_components_changed: pyqtSignal = pyqtSignal()
    group_component_edited: pyqtSignal = pyqtSignal(QGraphicsItem)
    left_clicked: pyqtSignal = pyqtSignal(QPointF)
    middle_clicked: pyqtSignal = pyqtSignal(QPointF)
    mouse_moved: pyqtSignal = pyqtSignal(QPointF)
    on_component_left_click: pyqtSignal = pyqtSignal(QGraphicsItem)
    on_component_right_click: pyqtSignal = pyqtSignal(QGraphicsItem)
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

    def __init__(self, background: Optional[QPixmap] = None, zoom_speed: float = 0.001, parent=None,
                 scene: Optional[QGraphicsScene] = None) -> None:
        """
        :param background: pixmap background for scene;
        :param zoom_speed: zoom speed;
        :param parent: parent;
        :param scene: scene for widget. In this argument you need to pass a scene from another widget if you need to
        display the scene on different widgets at once.
        """

        super().__init__(parent)
        self._components: List[QGraphicsItem] = []
        self._current_component: Optional[QGraphicsItem] = None
        self._drag_allowed: bool = True
        self._drawing_mode: DrawingMode = DrawingMode.EVERYWHERE
        self._edited_components: List[QGraphicsItem] = []
        self._edited_group: Optional[ComponentGroup] = None
        self._mouse_pos: QPointF = QPointF()
        self._operation: ExtendedScene.Operation = ExtendedScene.Operation.NO_ACTION
        self._pasted_components: List[BaseComponent] = []
        self._pen_to_edit: QPen = ut.create_cosmetic_pen(self.PEN_COLOR_TO_EDIT, self.PEN_WIDTH_TO_EDIT)
        self._point_increase_factor: float = self.POINT_INCREASE_FACTOR
        self._point_radius: float = self.POINT_RADIUS
        self._scale: float = 1.0
        self._scene_mode: SceneMode = SceneMode.NORMAL
        self._shift_pressed: bool = False
        self._zoom_speed: float = zoom_speed

        self._set_scene(scene)
        self.set_background(background)

        self._animation_timer: QTimer = QTimer()
        self._animation_timer.start(ExtendedScene.UPDATE_INTERVAL_MS)

        self._add_rubber_band()
        self._set_view_params()
        self._create_shortcuts()
        self._create_scale_sending_timer()

    @pyqtSlot()
    def _send_scale(self) -> None:
        self.scale_changed.emit(self._scale)

    @property
    def background(self) -> Optional[QGraphicsPixmapItem]:
        """
        :return: graphic scene background element.
        """

        if hasattr(self.scene(), "background"):
            return getattr(self.scene(), "background")

        return None

    def _add_edited_components_to_group(self) -> Optional[ComponentGroup]:
        """
        :return: a group of components into which all editable components are combined.
        """

        if not self._edited_components:
            group = None
        else:
            group = self._edited_group or ComponentGroup()
            for item in self._edited_components[:]:
                self.remove_component(item)
                item.setFlag(QGraphicsItem.ItemIsMovable, item.draggable)
                item.setFlag(QGraphicsItem.ItemIsSelectable, item.selectable)
                group.addToGroup(item)
            self.add_component(group)

        self._edited_group = None
        self._edited_components.clear()
        return group

    def _add_rubber_band(self) -> None:
        self._rubber_band: RubberBand = RubberBand()
        self._animation_timer.timeout.connect(self._rubber_band.update_selection)
        self.scene().addItem(self._rubber_band)

        self._tmp_rubber_band: QRubberBand = QRubberBand(QRubberBand.Rectangle, self)
        self._tmp_rubber_band_origin: QPoint = QPoint()

    def _change_component_draggability_according_scene_flag(self, component: QGraphicsItem) -> None:
        """
        :param component: the component that needs to be made movable or non-movable.
        """

        draggable = component.draggable if self._drag_allowed else False
        component.setFlag(QGraphicsItem.ItemIsMovable, draggable)

    def _connect_component_to_signals(self, component: QGraphicsItem) -> None:
        """
        :param component: component to be connected to scene signals.
        """

        if isinstance(component, BaseComponent):
            self.scale_changed.connect(component.update_scale)
            component.allow_drag(self._drag_allowed)
            component.set_scene_mode(self._scene_mode)
            self.scene_mode_changed.connect(component.set_scene_mode)
            component.selection_signal.connect(self._handle_component_selection_changed)

        if isinstance(component, RectComponent):
            self._animation_timer.timeout.connect(component.update_selection)
        elif isinstance(component, ComponentGroup):
            component.set_animation_timer(self._animation_timer)

        self._scale_sending_timer.start()
        logger.debug("Signals are connected to %s", component)

    def _create_scale_sending_timer(self) -> None:
        self._scale_sending_timer: QTimer = QTimer()
        self._scale_sending_timer.setSingleShot(True)
        self._scale_sending_timer.setInterval(ExtendedScene.UPDATE_INTERVAL_MS)
        self._scale_sending_timer.timeout.connect(self._send_scale)

    def _create_shortcuts(self) -> None:
        self._combination_and_slots = {Qt.CTRL + Qt.Key_C: self.copy_selected_components,
                                       Qt.CTRL + Qt.Key_X: self.cut_selected_components,
                                       Qt.Key_Delete: self.delete_selected_components,
                                       Qt.CTRL + Qt.Key_V: self.paste_copied_components}
        self._shortcuts: Dict[int, QShortcut] = dict()
        for combination, slot in self._combination_and_slots.items():
            shortcut = QShortcut(QKeySequence(combination), self)
            shortcut.setContext(Qt.WindowShortcut)
            shortcut.activated.connect(slot)
            self._shortcuts[combination] = shortcut

    def _enable_shortcuts(self) -> None:
        for combination, shortcut in self._shortcuts.items():
            shortcut.activated.connect(self._combination_and_slots[combination])

    def _finish_create_point_component_by_mouse(self) -> None:
        self._current_component.setSelected(False)
        self.scene().removeItem(self._current_component)
        modified_component = self._modify_component_to_add_to_scene(self._current_component)
        if modified_component:
            self.add_component(modified_component)
            self._edited_components.append(modified_component)

        self._current_component = None
        self._operation = ExtendedScene.Operation.NO_ACTION

    def _finish_create_rect_component_by_mouse(self) -> None:
        self.scene().removeItem(self._current_component)
        if self._current_component.check_big_enough():
            self._current_component.fix_mode(RectComponent.Mode.NO_ACTION)
            modified_component = self._modify_component_to_add_to_scene(self._current_component)
            if modified_component:
                self.add_component(modified_component)
                self._edited_components.append(modified_component)

        self._current_component = None
        self._operation = ExtendedScene.Operation.NO_ACTION

    def _get_clicked_item(self, event: QMouseEvent) -> Optional[QGraphicsItem]:
        """
        :param event: mouse event.
        :return: a component that is located at the point specified by the mouse.
        """

        for item in self.items(event.pos()):
            if isinstance(item, BaseComponent) and not isinstance(item, RubberBand):
                return item.group() if item.group() else item

        return None

    def _get_zoom_factor(self, event: QWheelEvent) -> float:
        """
        :param event: wheel event.
        :return: zoom factor.
        """

        zoom_factor = 1.0
        zoom_factor += event.angleDelta().y() * self._zoom_speed
        return zoom_factor

    def _handle_component_creation_by_mouse(self) -> None:
        if isinstance(self._current_component, PointComponent):
            self._current_component.setPos(self._mouse_pos)
        elif isinstance(self._current_component, RectComponent):
            self._current_component.resize_by_mouse(self._mouse_pos)

    def _handle_component_resize_by_mouse(self) -> None:
        self._current_component.resize_by_mouse(self._mouse_pos)

    def _handle_component_selection_by_rubber_band(self) -> None:
        rect = QRect(self._tmp_rubber_band_origin, self.mapFromScene(self._mouse_pos)).normalized()
        self._tmp_rubber_band.setGeometry(rect)

        self.remove_all_selections()
        path = QPainterPath()
        path.addRect(QRectF(self.mapToScene(self._tmp_rubber_band_origin), self._mouse_pos).normalized())
        self.scene().setSelectionArea(path)

    @pyqtSlot(bool)
    @ut.send_edited_components_changed_signal
    def _handle_component_selection_changed(self, selected: bool) -> None:
        """
        :param selected: if False, then the component has become not selected.
        """

        if not hasattr(self.sender(), "component") or selected:
            return

        component = self.sender().component
        if component in self._pasted_components:
            self._handle_pasted_component_deselection(component)
            self._set_editable_status_for_components()

    def _handle_pasted_component_deselection(self, component: BaseComponent) -> None:
        """
        :param component: a component that was pasted after copying and then became unselected.
        """

        self._pasted_components.remove(component)
        component.set_scene_mode(self._scene_mode)

        if self._scene_mode is SceneMode.EDIT_GROUP and isinstance(component, ComponentGroup):
            components = self._handle_pasted_component_group_deselection_in_edit_group(component)
        else:
            components = [component]

        for component in components:
            if component and self._scene_mode is not SceneMode.NORMAL:
                self._edited_components.append(component)
            self.component_pasted.emit(component)

    def _handle_pasted_component_group_deselection_in_edit_group(self, group: ComponentGroup) -> List[BaseComponent]:
        """
        :param group: a component group that was pasted after copying and then became unselected.
        :return: list of components that need to be pasted as a result.
        """

        self.remove_component(group)
        child_components = []
        for item in group.childItems():
            group.removeFromGroup(item)
            child_components.append(item)
            self.add_component(item)
        return child_components

    def _handle_mouse_left_button_press(self, item: Optional[QGraphicsItem], event: QMouseEvent, pos: QPointF) -> None:
        """
        :param item: component clicked by mouse;
        :param event: mouse event;
        :param pos: mouse position.
        """

        self._rubber_band.hide()
        if item:
            self.on_component_left_click.emit(item)
        else:
            self.left_clicked.emit(pos)

        if (self._scene_mode in (SceneMode.EDIT, SceneMode.EDIT_GROUP) and item in self._edited_components and
                self._set_resize_mode_for_rect_component(item)):
            return

        if item:
            self._select_group_component_with_mouse_left_button_press(item, event)
            self._set_drag_component_mode()
            return

        # We are in drag board mode now
        self.remove_all_selections()
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self._operation = ExtendedScene.Operation.DRAG

    def _handle_mouse_left_button_release(self) -> None:
        if self._operation is ExtendedScene.Operation.DRAG_COMPONENT:
            for item in self.scene().selectedItems():
                self.component_moved.emit(item)
        elif self._operation is ExtendedScene.Operation.RESIZE_COMPONENT:
            self._current_component.setFlag(QGraphicsItem.ItemIsMovable, True)
            self._current_component = None

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

        if self._scene_mode is SceneMode.NORMAL:
            self._set_select_component_mode(pos)
        elif self._scene_mode in (SceneMode.EDIT, SceneMode.EDIT_GROUP):
            if self._shift_pressed:
                self._start_create_point_component_by_mouse(pos)
            else:
                self._start_create_rect_component_by_mouse(pos)

    @ut.send_edited_components_changed_signal
    def _handle_mouse_right_button_release(self, pos: QPoint) -> None:
        """
        :param pos: mouse position.
        """

        if self._scene_mode is SceneMode.NORMAL and self._operation is ExtendedScene.Operation.SELECT_COMPONENT:
            self._tmp_rubber_band.hide()
            rubber_band_changed = self._set_new_rect_for_rubber_band()
            if not rubber_band_changed:
                self._send_custom_context_menu_signal(pos)
        elif self._scene_mode in (SceneMode.EDIT, SceneMode.EDIT_GROUP):
            if isinstance(self._current_component, PointComponent):
                self._finish_create_point_component_by_mouse()
            elif isinstance(self._current_component, RectComponent):
                self._finish_create_rect_component_by_mouse()

    def _modify_component_to_add_to_scene(self, component: QGraphicsItem) -> Optional[QGraphicsItem]:
        """
        :param component: component to be added to the scene.
        :return: a modified component that can be added to the scene.
        """

        if self._drawing_mode is DrawingMode.EVERYWHERE:
            return component

        if not self.background:
            return None

        if isinstance(component, ComponentGroup):
            return self._modify_group_component_to_add_to_background_only(component)

        if isinstance(component, PointComponent):
            return self._modify_point_component_to_add_to_background_only(component)

        if isinstance(component, RectComponent):
            return self._modify_rect_component_to_add_to_background_only(component)

        return component

    def _modify_group_component_to_add_to_background_only(self, group: ComponentGroup) -> Optional[ComponentGroup]:
        """
        :param group: component group to be added to the scene.
        :return: a modified component group that can be added to the scene.
        """

        group.limit_size_to_background(self.background)
        if not group.childItems():
            return None

        return group

    def _modify_point_component_to_add_to_background_only(self, component: PointComponent) -> Optional[PointComponent]:
        """
        :param component: point component to be added to the scene.
        :return: a modified point component that can be added to the scene.
        """

        return component if self.background.contains(component.pos()) else None

    def _modify_rect_component_to_add_to_background_only(self, component: RectComponent) -> Optional[RectComponent]:
        """
        :param component: rectangle component to be added to the scene.
        :return: a modified rectangle component that can be added to the scene.
        """

        rect = component.mapRectToScene(component.rect())
        background_rect = self.background.sceneBoundingRect()
        modified_rect = ut.fit_rect_to_background(background_rect, rect)
        if modified_rect:
            component.setPos(modified_rect.topLeft())
            component.setRect(QRectF(QPointF(0, 0), modified_rect.size()))
            return component

        return None

    def _paste_copied_components(self, copied_components: List[Dict[str, Any]]) -> None:
        """
        :param copied_components: list of copied components with their positions to be pasted.
        """

        if self._operation is not ExtendedScene.Operation.NO_ACTION or not copied_components:
            return

        self.remove_all_selections()
        left_top = ut.get_left_top_pos([QPointF(*component_data["pos"]) for component_data in copied_components])

        for component_data in copied_components:
            component_class = ut.get_class_by_name(component_data["class"])
            if not component_class or not hasattr(component_class, "create_from_json"):
                continue

            component = component_class.create_from_json(component_data)
            if not component:
                continue

            component.set_position_after_paste(self._mouse_pos, QPointF(*component_data["pos"]), left_top)
            self.add_component(component)
            component.setFlag(QGraphicsItem.ItemIsMovable, True)
            component.setFlag(QGraphicsItem.ItemIsSelectable, True)
            component.setSelected(True)
            self._pasted_components.append(component)

    def _remove_items_from_edited_group(self) -> None:
        items = self.scene().selectedItems()
        self._edited_group = items[0] if len(items) == 1 and isinstance(items[0], ComponentGroup) else None

        for component in self._components[:]:
            if component is not self._edited_group:
                component.setFlag(QGraphicsItem.ItemIsMovable, False)
                component.setFlag(QGraphicsItem.ItemIsSelectable, False)

        self._edited_components = []
        if self._edited_group:
            for child_item in self._edited_group.set_edit_group_mode():
                self.add_component(child_item)
                self._edited_components.append(child_item)
                child_item.setFlag(QGraphicsItem.ItemIsMovable, True)
                child_item.setFlag(QGraphicsItem.ItemIsSelectable, True)

            self.remove_component(self._edited_group)

    def _restore_editable_status_for_components(self) -> None:
        for component in self._edited_components:
            try:
                component.set_editable(False)
            except Exception:
                logger.debug("Failed to call 'set_editable' method on component %s", component)

    def _select_group_component_with_mouse_left_button_press(self, item: QGraphicsItem, event: QMouseEvent) -> None:
        """
        :param item: component clicked by mouse;
        :param event: mouse event.
        """

        if not isinstance(item, ComponentGroup) or int(event.modifiers()) & Qt.ControlModifier:
            return

        if not item.isSelected():
            self.remove_all_selections()

        item.setSelected(True)

    def _send_custom_context_menu_signal(self, pos: QPoint) -> None:
        """
        :param pos: mouse position.
        """

        if self.contextMenuPolicy() == Qt.CustomContextMenu:
            self.custom_context_menu_requested.emit(pos)

    def _set_background(self, background: Optional[QPixmap] = None) -> None:
        """
        :param background: pixmap background for scene.
        """

        self.scene().background = self.scene().addPixmap(background) if background else None

    def _set_drag_component_mode(self) -> None:
        self._operation = ExtendedScene.Operation.DRAG_COMPONENT

    def _set_editable_status_for_components(self) -> None:
        for component in self._edited_components:
            try:
                component.set_editable(True, self._pen_to_edit)
            except Exception:
                logger.debug("Failed to call 'set_editable' method on component %s", component)

    def _set_new_rect_for_rubber_band(self) -> bool:
        """
        :return: True if the rubber band geometry has been changed, otherwise False.
        """

        top_left = self._tmp_rubber_band.pos()
        top_left = self.mapToScene(top_left)
        bottom_right = QPoint(self._tmp_rubber_band.x() + self._tmp_rubber_band.width(),
                              self._tmp_rubber_band.y() + self._tmp_rubber_band.height())
        bottom_right = self.mapToScene(bottom_right)
        rect = QRectF(top_left, bottom_right)
        return self._rubber_band.set_rect(rect)

    def _set_no_action_mode(self) -> None:
        self._operation = ExtendedScene.Operation.NO_ACTION

    def _set_resize_mode_for_rect_component(self, item: RectComponent) -> bool:
        """
        :param item: component that will be resized.
        :return: True if the mode is set.
        """

        if (isinstance(item, RectComponent) and item.isSelected() and not item.is_in_group() and
                item.check_in_resize_mode()):
            item.go_to_resize_mode()
            self._current_component = item
            self._operation = ExtendedScene.Operation.RESIZE_COMPONENT
            return True

        return False

    def _set_scene(self, scene: Optional[QGraphicsScene]) -> None:
        """
        :param scene: scene for widget.
        """

        if not scene:
            scene = QGraphicsScene()
            scene.setItemIndexMethod(QGraphicsScene.NoIndex)
        self.setScene(scene)

    def _set_select_component_mode(self, pos: QPointF) -> None:
        """
        :param pos: mouse position.
        """

        self._tmp_rubber_band_origin = self.mapFromScene(pos)
        self._tmp_rubber_band.setGeometry(QRect(self._tmp_rubber_band_origin, QSize()))
        self._tmp_rubber_band.show()
        self._operation = ExtendedScene.Operation.SELECT_COMPONENT

    def _set_view_params(self) -> None:
        self.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setBackgroundBrush(QBrush(QColor(0, 0, 0)))
        self.setFrameShape(QFrame.NoFrame)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)

    def _start_create_point_component_by_mouse(self, pos: QPointF) -> None:
        """
        :param pos: mouse position.
        """

        if self._current_component:
            self.scene().removeItem(self._current_component)

        self._current_component = PointComponent(self._point_radius, scale=self._scale,
                                                 increase_factor=self._point_increase_factor)
        self._current_component.setPos(pos)
        self._current_component.set_editable(True, self._pen_to_edit)
        self.scene().addItem(self._current_component)
        self._operation = ExtendedScene.Operation.CREATE_COMPONENT

    def _start_create_rect_component_by_mouse(self, pos: QPointF) -> None:
        """
        :param pos: mouse position.
        """

        if self._current_component:
            self.scene().removeItem(self._current_component)

        self._current_component = RectComponent(QRectF(QPointF(0, 0), QPointF(0, 0)))
        self._current_component.setPos(pos)
        self._current_component.fix_mode(RectComponent.Mode.RESIZE_ANY)
        self._current_component.set_editable(True, self._pen_to_edit)
        self.scene().addItem(self._current_component)
        self._operation = ExtendedScene.Operation.CREATE_COMPONENT

    def add_component(self, component: QGraphicsItem) -> None:
        """
        :param component: component to be added to the scene.
        """

        self._components.append(component)
        self.scene().addItem(component)
        self._connect_component_to_signals(component)
        logger.debug("%s added to the scene", component)

    def allow_drag(self, allow: bool = True) -> None:
        """
        :param allow: if True, then components are allowed to be moved around the scene.
        """

        self._drag_allowed = allow
        for component in self._components:
            if isinstance(component, BaseComponent):
                component.allow_drag(allow)

    def clear_scene(self) -> None:
        self.scene().clear()
        self._components = []
        self._set_background()
        self.resetTransform()

    def copy_selected_components(self) -> None:
        mime = QMimeData()
        copied_components = [item.convert_to_json() for item in self.scene().selectedItems()
                             if isinstance(item, BaseComponent)]
        encoded_data = json.dumps(copied_components).encode("utf-8")
        mime.setData(self.MIME_TYPE, encoded_data)
        clipboard = qApp.instance().clipboard()
        clipboard.setMimeData(mime)

    def cut_selected_components(self) -> None:
        self.copy_selected_components()
        self.delete_selected_components()

    @ut.send_edited_components_changed_signal
    def delete_selected_components(self) -> None:
        for item in self.scene().selectedItems():
            self.remove_component(item)
            self.component_deleted.emit(item)
            try:
                self._edited_components.remove(item)
            except ValueError:
                pass

    def disable_shortcuts(self) -> None:
        for combination, shortcut in self._shortcuts.items():
            try:
                shortcut.activated.disconnect(self._combination_and_slots[combination])
            except TypeError:
                ...

    def enable_shortcuts(self) -> None:
        self.disable_shortcuts()
        self._enable_shortcuts()

    def fit_in_view(self) -> None:
        self.fitInView(self.sceneRect(), Qt.KeepAspectRatioByExpanding)

    def get_background_size(self) -> QSizeF:
        """
        :return: background image size.
        """

        return self.background.boundingRect().size() if self.background else QSizeF()

    def get_visible_rubber_band_rect(self) -> Optional[QRectF]:
        """
        :return: boundaries of the visible selected area. If the rubber band is invisible, then None is returned.
        """

        rubber_band_rect = self._rubber_band.rect()
        if self._rubber_band.isVisible() and rubber_band_rect.height() and rubber_band_rect.width():
            return rubber_band_rect

        return None

    def hide_rubber_band_after_mouse_release(self) -> None:
        """
        The method sets the rubber band display mode, which hides the rubber band after releasing the mouse button.
        """

        self._rubber_band.set_display_mode(RubberBand.DisplayMode.HIDE)

    def is_drag_allowed(self) -> bool:
        """
        :return: if True, then components are allowed to be moved around the scene.
        """

        return self._drag_allowed

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """
        :param event: key event.
        """

        if event.key() == Qt.Key_Shift and self._scene_mode is not SceneMode.NORMAL:
            self._shift_pressed = True

    def keyReleaseEvent(self, event: QKeyEvent) -> None:
        """
        :param event: key event.
        """

        if event.key() == Qt.Key_Shift and self._scene_mode is not SceneMode.NORMAL:
            self._shift_pressed = False

    def limit_rubber_band_size_to_background(self, limit: bool) -> None:
        """
        :param limit: if True, then it is needed to limit the size of the rubber band within the background.
        """

        self._rubber_band.limit_size_to_background(limit)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """
        :param event: mouse event.
        """

        self._mouse_pos = self.mapToScene(event.pos())
        self.mouse_moved.emit(self._mouse_pos)
        if self._operation is ExtendedScene.Operation.CREATE_COMPONENT:
            self._handle_component_creation_by_mouse()
            event.accept()
            return

        if self._operation is ExtendedScene.Operation.SELECT_COMPONENT:
            self._handle_component_selection_by_rubber_band()
            event.accept()
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
            self._handle_mouse_left_button_press(item, event, pos)
        elif event.button() == Qt.MiddleButton:
            self._handle_mouse_middle_button_press(pos)
        elif event.button() == Qt.RightButton:
            self._handle_mouse_right_button_press(item, pos)
            event.accept()
            return

        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """
        :param event: mouse event.
        """

        if event.button() == Qt.LeftButton:
            self._handle_mouse_left_button_release()
        elif event.button() == Qt.RightButton:
            self._handle_mouse_right_button_release(event.pos())

        super().mouseReleaseEvent(event)

        self.setDragMode(QGraphicsView.NoDrag)
        self._set_no_action_mode()

    def paste_copied_components(self) -> None:
        clipboard = qApp.instance().clipboard()
        mime_data = clipboard.mimeData()
        if not mime_data.hasFormat(self.MIME_TYPE):
            return

        copied_components = json.loads(mime_data.data(self.MIME_TYPE).data())
        self._paste_copied_components(copied_components)

    def remove_all_selections(self, components: Optional[List[QGraphicsItem]] = None) -> None:
        """
        :param components: list of components that need to be deselected.
        """

        components = components or self._components
        for item in components[:]:
            item.setSelected(False)

    def remove_component(self, component: QGraphicsItem) -> None:
        """
        :param component: component to be removed from the scene.
        """

        self._components.remove(component)
        self.scene().removeItem(component)
        self.scale_changed.disconnect(component.update_scale)
        self.scene_mode_changed.disconnect(component.set_scene_mode)
        component.selection_signal.disconnect(self._handle_component_selection_changed)
        if isinstance(component, RectComponent):
            self._animation_timer.timeout.disconnect(component.update_selection)

    def scale_to_window_size(self, size: QSize) -> None:
        """
        Scale to window size.
        For example, if you have window 600x600 and workspace background image 1200x1200, image will be scaled in 4x.
        :param size: window size.
        """

        if self.background:
            factor_x = size.width() / self.background.pixmap().width()
            factor_y = size.height() / self.background.pixmap().height()
            factor = max(min(factor_x, factor_y), ExtendedScene.MIN_SCALE)
            self.resetTransform()
            self._scale = factor
            self.zoom(factor, QPoint(0, 0))

    def set_background(self, background: QPixmap) -> None:
        """
        :param background: new pixmap background for scene.
        """

        if self.background:
            raise ValueError("Call 'clear_scene' first!")

        self._set_background(background)

    def set_default_point_component_parameters(self, radius: Optional[float] = None,
                                               increase_factor: Optional[float] = None) -> None:
        """
        :param radius: radius for the point components to be created;
        :param increase_factor: increase factor for point components to be created.
        """

        self._point_increase_factor = increase_factor or self.POINT_INCREASE_FACTOR
        self._point_radius = radius or self.POINT_RADIUS

    def set_drawing_mode(self, drawing_mode: DrawingMode) -> None:
        """
        :param drawing_mode: new drawing mode.
        """

        self._drawing_mode = drawing_mode

    @ut.send_edited_components_changed_signal
    def set_scene_mode(self, mode: SceneMode) -> None:
        """
        :param mode: new scene mode.
        """

        self._restore_editable_status_for_components()

        if self._scene_mode is SceneMode.EDIT_GROUP:
            group = self._add_edited_components_to_group()
            if group:
                self.group_component_edited.emit(group)

        self._scene_mode = mode
        self.scene_mode_changed.emit(mode)

        if mode is SceneMode.EDIT:
            self._edited_components = self._components[:]
        elif mode is SceneMode.EDIT_GROUP:
            self._remove_items_from_edited_group()
        else:
            self._edited_components = []

        self._set_editable_status_for_components()

    def show_rubber_band_after_mouse_release(self) -> None:
        """
        The method sets the rubber band display mode, in which the rubber band remains visible after releasing the
        mouse button.
        """

        self._rubber_band.set_display_mode(RubberBand.DisplayMode.SHOW)

    def wheelEvent(self, event: QWheelEvent) -> None:
        """
        :param event: wheel event.
        """

        zoom_factor = self._get_zoom_factor(event)
        if self._scale * zoom_factor < ExtendedScene.MIN_SCALE and zoom_factor < 1.0:  # minimum allowed zoom
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
