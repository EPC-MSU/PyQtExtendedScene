from enum import auto, Enum
from typing import List, Optional
from PyQt5.QtCore import pyqtSignal, QPoint, QPointF, QRect, QSize, Qt, QTimer
from PyQt5.QtGui import QBrush, QColor, QMouseEvent, QPixmap, QResizeEvent, QWheelEvent
from PyQt5.QtWidgets import QFrame, QGraphicsPixmapItem, QGraphicsScene, QGraphicsView, QRubberBand
from .abstractcomponent import AbstractComponent
from .scalablecomponent import ScalableComponent


class ExtendedScene(QGraphicsView):

    MINIMUM_SCALE: int = 0.1
    UPDATE_INTERVAL: int = 400
    on_component_left_click: pyqtSignal = pyqtSignal(AbstractComponent)
    on_component_right_click: pyqtSignal = pyqtSignal(AbstractComponent)
    on_component_moved: pyqtSignal = pyqtSignal(AbstractComponent)
    on_middle_click: pyqtSignal = pyqtSignal()
    on_right_click: pyqtSignal = pyqtSignal(QPointF)
    scale_changed: pyqtSignal = pyqtSignal(float)

    class State(Enum):
        DRAG = auto()
        DRAG_COMPONENT = auto()
        NO = auto()
        SELECT = auto()

    def __init__(self, background: Optional[QPixmap] = None, zoom_speed: float = 0.001, parent=None) -> None:
        """
        :param background: pixmap background for scene;
        :param zoom_speed:
        :param parent: parent.
        """

        super().__init__(parent)
        self._scale: float = 1.0
        self._zoom_speed: float = zoom_speed

        self._components: List[AbstractComponent] = []
        self._current_component: Optional[AbstractComponent] = None
        self._drag_allowed: bool = True
        self._rubber_band: QRubberBand = QRubberBand(QRubberBand.Rectangle, self)
        self._rubber_band.hide()
        self._start_pos: Optional[QPointF] = None
        self._state: ExtendedScene.State = ExtendedScene.State.NO

        self._scene: QGraphicsScene = QGraphicsScene()
        self._background: Optional[QGraphicsPixmapItem] = self._scene.addPixmap(background) if background else None
        self.setScene(self._scene)

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

        self._timer: QTimer = QTimer()
        self._timer.start(ExtendedScene.UPDATE_INTERVAL)

    def _get_clicked_item(self, event: QMouseEvent) -> Optional[AbstractComponent]:
        """
        :param event: mouse event.
        :return: a component that is located at the point specified by the mouse.
        """

        for item in self.items(event.pos()):
            if isinstance(item, AbstractComponent):
                return item

        return None

    def _handle_mouse_left_button_press(self, event: QMouseEvent, item: AbstractComponent) -> None:
        """
        :param event: mouse event;
        :param item: component clicked by mouse.
        """

        self._start_pos = self.mapToScene(event.pos())

        if item:
            self.on_component_left_click.emit(item)

            if item.selectable:
                if item.unique_selection:
                    self.remove_all_selections()
                item.select(True)

            if item.draggable and self._drag_allowed:
                self._state = ExtendedScene.State.DRAG_COMPONENT
                self._current_component = item
            return

        # We are in drag board mode now
        self._state = ExtendedScene.State.DRAG
        self.setDragMode(QGraphicsView.ScrollHandDrag)

    def _handle_mouse_middle_button_press(self, event: QMouseEvent) -> None:
        """
        :param event: mouse event.
        """

        self.on_middle_click.emit()
        self._start_pos = event.pos()
        self._rubber_band.setGeometry(QRect(self._start_pos, QSize()))
        self._rubber_band.show()
        self._state = ExtendedScene.State.SELECT

    def _handle_mouse_middle_button_release(self, event: QMouseEvent) -> None:
        """
        :param event: mouse event.
        """

        self._select_components(self._rubber_band.geometry())
        self._rubber_band.hide()
        self._state = ExtendedScene.State.NO

    def _select_components(self, rect: QRect) -> None:
        for item in self.items(rect):
            if isinstance(item, AbstractComponent):
                item.select(True)

    def _handle_mouse_right_button_press(self, event: QMouseEvent, item: AbstractComponent) -> None:
        """
        :param event: mouse event;
        :param item: component clicked by mouse.
        """

        if item:
            self.on_component_right_click.emit(item)
            return

        self.on_right_click.emit(self.mapToScene(event.pos()))

    def add_component(self, component: AbstractComponent) -> None:
        """
        :param component: component to be added to the scene.
        """

        self._components.append(component)
        self._scene.addItem(component)
        component.update_scale(self._scale)
        self.scale_changed.connect(component.update_scale)
        if isinstance(component, ScalableComponent):
            self._timer.timeout.connect(component.update_selection)

    def all_components(self, class_filter: type = object) -> List[AbstractComponent]:
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

    def is_drag_allowed(self) -> bool:
        """
        :return: if True, then components are allowed to be moved around the scene.
        """

        return self._drag_allowed

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """
        :param event: mouse event.
        """

        if self._state == ExtendedScene.State.DRAG:
            delta = self.mapToScene(event.pos()) - self._start_pos
            self.move(delta)
        elif self._state == ExtendedScene.State.DRAG_COMPONENT:
            self._current_component.setPos(self.mapToScene(event.pos()))
        elif self._state == ExtendedScene.State.SELECT:
            self._rubber_band.setGeometry(QRect(self._start_pos, event.pos()).normalized())

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """
        :param event: mouse event.
        """

        # Check for clicked pin
        item = self._get_clicked_item(event)

        if event.button() & Qt.LeftButton:
            self._handle_mouse_left_button_press(event, item)

        if event.button() & Qt.MiddleButton:
            self._handle_mouse_middle_button_press(event)

        if event.button() & Qt.RightButton:
            self._handle_mouse_right_button_press(event, item)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """
        :param event: mouse event.
        """

        if event.button() & Qt.LeftButton:
            self.setDragMode(QGraphicsView.NoDrag)

            if self._state == ExtendedScene.State.DRAG_COMPONENT:
                if self._current_component:
                    self.on_component_moved.emit(self._current_component)

            self._state = ExtendedScene.State.NO

        if event.button() & Qt.MiddleButton:
            self._handle_mouse_middle_button_release(event)

    def move(self, delta: QPoint) -> None:
        """
        :param delta: offset to which the scene should be moved.
        """

        # Note: Workaround! See:
        # - https://bugreports.qt.io/browse/QTBUG-7328
        # - https://stackoverflow.com/questions/14610568/how-to-use-the-qgraphicsviews-translate-function
        anchor = self.transformationAnchor()
        self.setTransformationAnchor(QGraphicsView.NoAnchor)  # Override transformation anchor
        self.translate(delta.x(), delta.y())
        self.setTransformationAnchor(anchor)  # Restore old anchor

    def remove_all_selections(self) -> None:
        for item in self._components:
            item.select(False)

    def remove_component(self, component: AbstractComponent) -> None:
        """
        :param component: component to be removed from the scene.
        """

        self._components.remove(component)
        self._scene.removeItem(component)
        self.scale_changed.disconnect(component.update_scale)
        if isinstance(component, ScalableComponent):
            self._timer.timeout.disconnect(component.update_selection)

    def resizeEvent(self, event: QResizeEvent) -> None:
        pass

    def scale_to_window_size(self, x: float, y: float) -> None:
        """
        Scale to window size.
        For example, if you have window 600x600 and workspace background image 1200x1200, image will be scaled in 4x.
        :param x: window width;
        :param y: window height.
        """

        factor_x = x / self._background.pixmap().width()
        factor_y = y / self._background.pixmap().height()
        factor = max(min(factor_x, factor_y), self.MINIMUM_SCALE)
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
        if self._scale * zoom_factor < self.MINIMUM_SCALE and zoom_factor < 1.0:  # minimum allowed zoom
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
