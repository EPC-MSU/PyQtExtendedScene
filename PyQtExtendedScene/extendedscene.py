from enum import auto, Enum
from typing import List, Optional, Tuple
from PyQt5.QtCore import pyqtSignal, QPoint, QPointF, QRectF, Qt, QTimer
from PyQt5.QtGui import QBrush, QColor, QKeySequence, QMouseEvent, QPixmap, QWheelEvent
from PyQt5.QtWidgets import QFrame, QGraphicsItem, QGraphicsPixmapItem, QGraphicsScene, QGraphicsView, QShortcut
from .abstractcomponent import AbstractComponent
from .scalablecomponent import ScalableComponent
from .pointcomponent import PointComponent


class ExtendedScene(QGraphicsView):

    MIN_SCALE: float = 0.1
    UPDATE_INTERVAL: int = 10  # msec
    on_component_left_click: pyqtSignal = pyqtSignal(QGraphicsItem)
    on_component_right_click: pyqtSignal = pyqtSignal(QGraphicsItem)
    on_component_moved: pyqtSignal = pyqtSignal(QGraphicsItem)
    on_middle_click: pyqtSignal = pyqtSignal()
    on_right_click: pyqtSignal = pyqtSignal(QPointF)
    scale_changed: pyqtSignal = pyqtSignal(float)

    class State(Enum):
        """
        Enumerating possible widget states.
        """

        CREATE_COMPONENT = auto()
        DRAG = auto()
        DRAG_COMPONENT = auto()
        NO = auto()
        RESIZE_COMPONENT = auto()
        SELECT_COMPONENT = auto()

    def __init__(self, background: Optional[QPixmap] = None, zoom_speed: float = 0.001, parent=None) -> None:
        """
        :param background: pixmap background for scene;
        :param zoom_speed:
        :param parent: parent.
        """

        super().__init__(parent)
        self._scale: float = 1.0
        self._zoom_speed: float = zoom_speed

        self._components: List[QGraphicsItem] = []
        self._copied_components: List[Tuple[ScalableComponent, QPointF]] = []
        self._current_component: Optional[QGraphicsItem] = None
        self._drag_allowed: bool = True
        self._mouse_pos: QPointF = QPointF()
        self._state: ExtendedScene.State = ExtendedScene.State.NO

        self._scene: QGraphicsScene = QGraphicsScene()
        self.setScene(self._scene)
        self._background: Optional[QGraphicsPixmapItem] = self._scene.addPixmap(background) if background else None

        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setBackgroundBrush(QBrush(QColor(0, 0, 0)))
        self.setFrameShape(QFrame.NoFrame)
        # Mouse
        self.setMouseTracking(True)
        # For keyboard events
        self.setFocusPolicy(Qt.StrongFocus)

        self._copy_shortcut: QShortcut = QShortcut(QKeySequence(Qt.CTRL + Qt.Key_C), self)
        self._copy_shortcut.setContext(Qt.WindowShortcut)
        self._copy_shortcut.activated.connect(self.copy_selected_components)
        self._paste_shortcut: QShortcut = QShortcut(QKeySequence(Qt.CTRL + Qt.Key_V), self)
        self._paste_shortcut.setContext(Qt.WindowShortcut)
        self._paste_shortcut.activated.connect(self.paste_copied_components)

        self._timer: QTimer = QTimer()
        self._timer.start(ExtendedScene.UPDATE_INTERVAL)

    def _get_clicked_item(self, event: QMouseEvent) -> Optional[QGraphicsItem]:
        """
        :param event: mouse event.
        :return: a component that is located at the point specified by the mouse.
        """

        for item in self.items(event.pos()):
            if isinstance(item, (AbstractComponent, ScalableComponent)):
                return item

        return None

    def _handle_mouse_left_button_press(self, item: Optional[QGraphicsItem]) -> None:
        """
        :param item: component clicked by mouse.
        """

        if (isinstance(item, ScalableComponent) and item.isSelected() and
                item.mode not in (ScalableComponent.Mode.MOVE, ScalableComponent.Mode.NO)):
            item.setFlag(QGraphicsItem.ItemIsMovable, False)
            self._current_component = item
            self._current_component.fix_mode(item.mode)
            self._state = ExtendedScene.State.RESIZE_COMPONENT
            return

        if item:
            self.on_component_left_click.emit(item)
            if item.selectable:
                if not item.isSelected() and item.unique_selection:
                    self.remove_all_selections()
            self._state = ExtendedScene.State.DRAG_COMPONENT
            return

        # We are in drag board mode now
        self.remove_all_selections()
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self._state = ExtendedScene.State.DRAG

    def _handle_mouse_left_button_release(self) -> None:
        self.setDragMode(QGraphicsView.NoDrag)

        if self._state == ExtendedScene.State.DRAG_COMPONENT:
            if self._scene.selectedItems():
                for item in self._scene.selectedItems():
                    self.on_component_moved.emit(item)
        elif self._state == ExtendedScene.State.RESIZE_COMPONENT:
            for item in self._scene.selectedItems():
                item.setFlag(QGraphicsItem.ItemIsMovable, True)

        self._state = ExtendedScene.State.NO

    def _handle_mouse_middle_button_press(self) -> None:
        self.on_middle_click.emit()
        self.setDragMode(QGraphicsView.RubberBandDrag)
        self._state = ExtendedScene.State.SELECT_COMPONENT

    def _handle_mouse_middle_button_release(self) -> None:
        self.setDragMode(QGraphicsView.NoDrag)
        self._state = ExtendedScene.State.NO

    def _handle_mouse_right_button_press(self, event: QMouseEvent, item: QGraphicsItem) -> None:
        """
        :param event: mouse event;
        :param item: component clicked by mouse.
        """

        if item:
            self.on_component_right_click.emit(item)
            return

        pos = self.mapToScene(event.pos())
        self._current_component = ScalableComponent(QRectF(QPointF(0, 0), QPointF(0, 0)))
        self._current_component.setPos(pos)
        self._scene.addItem(self._current_component)
        self._current_component.fix_mode(ScalableComponent.Mode.RESIZE_ANY)
        self.on_right_click.emit(pos)
        self._state = ExtendedScene.State.CREATE_COMPONENT

    def _handle_mouse_right_button_release(self) -> None:
        if self._current_component:
            self._scene.removeItem(self._current_component)
            if self._current_component.check_big_enough():
                self._current_component.fix_mode(ScalableComponent.Mode.NO)
                self.add_component(self._current_component)
            self._current_component = None
        self._state = ExtendedScene.State.NO

    def add_component(self, component: QGraphicsItem) -> None:
        """
        :param component: component to be added to the scene.
        """

        self._components.append(component)
        self._scene.addItem(component)
        component.update_scale(self._scale)
        self.scale_changed.connect(component.update_scale)
        if isinstance(component, ScalableComponent):
            self._timer.timeout.connect(component.update_selection)

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
                                   if isinstance(item, (PointComponent, ScalableComponent))]

    def is_drag_allowed(self) -> bool:
        """
        :return: if True, then components are allowed to be moved around the scene.
        """

        return self._drag_allowed

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """
        :param event: mouse event.
        """

        self._mouse_pos = self.mapToScene(event.pos())
        if self._state in (ExtendedScene.State.CREATE_COMPONENT, ExtendedScene.State.RESIZE_COMPONENT):
            self._current_component.resize_by_mouse(self._mouse_pos)
        super().mouseMoveEvent(event)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """
        :param event: mouse event.
        """

        item = self._get_clicked_item(event)
        if event.button() == Qt.LeftButton:
            self._handle_mouse_left_button_press(item)
        elif event.button() == Qt.MiddleButton:
            self._handle_mouse_middle_button_press()
        elif event.button() == Qt.RightButton:
            self._handle_mouse_right_button_press(event, item)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """
        :param event: mouse event.
        """

        if event.button() == Qt.LeftButton:
            self._handle_mouse_left_button_release()
        elif event.button() == Qt.MiddleButton:
            self._handle_mouse_middle_button_release()
        elif event.button() == Qt.RightButton:
            self._handle_mouse_right_button_release()
        super().mouseReleaseEvent(event)

    def paste_copied_components(self) -> None:
        self.remove_all_selections()
        left, top = None, None
        for item, item_pos in self._copied_components:
            item_x, item_y = item_pos.x(), item_pos.y()
            if left is None or left > item_x:
                left = item_x
            if top is None or top > item_y:
                top = item_y

        for item, item_pos in self._copied_components:
            item_to_paste = item.copy()[0]
            new_item_x = self._mouse_pos.x() + item_pos.x() - left
            new_item_y = self._mouse_pos.y() + item_pos.y() - top
            item_to_paste.setPos(new_item_x, new_item_y)
            self.add_component(item_to_paste)
            item_to_paste.setSelected(True)

    def remove_all_selections(self) -> None:
        for item in self._components:
            item.setSelected(False)

    def remove_component(self, component: QGraphicsItem) -> None:
        """
        :param component: component to be removed from the scene.
        """

        self._components.remove(component)
        self._scene.removeItem(component)
        self.scale_changed.disconnect(component.update_scale)
        if isinstance(component, ScalableComponent):
            self._timer.timeout.disconnect(component.update_selection)

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
