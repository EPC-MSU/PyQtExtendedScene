from PyQt5 import QtCore
from PyQt5.QtCore import Qt, QPointF, QPoint
from PyQt5.QtGui import QBrush, QColor, QMouseEvent, QPixmap, QResizeEvent, QWheelEvent
from PyQt5.QtWidgets import QGraphicsView, QFrame, QGraphicsScene, QGraphicsItem
from typing import Optional, List
from enum import Enum, auto


class AbstractComponent(QGraphicsItem):

    def __init__(self, draggable: bool = True, selectable: bool = True, unique_selection: bool = True) -> None:
        """
        Abstract component.
        :param draggable: True if component can be dragged;
        :param selectable: True if component can be selected;
        :param unique_selection: True if selecting this component should reset all others selections
        ('selectable' must be set).
        """

        super().__init__()

        self._draggable: bool = draggable
        self._selectable: bool = selectable
        self._unique_selection: bool = unique_selection

    def select(self, selected: bool = True):
        pass

    def update_scale(self, scale: float):
        pass

    @property
    def draggable(self) -> bool:
        return self._draggable

    @property
    def selectable(self) -> bool:
        return self._selectable

    @property
    def unique_selection(self) -> bool:
        return self._unique_selection

    def paint(self, painter, option, widget=None):
        pass

    def boundingRect(self):
        # By default bounding rect of our object is a bounding rect of children items
        return self.childrenBoundingRect()


class ExtendedScene(QGraphicsView):

    on_component_left_click = QtCore.pyqtSignal(AbstractComponent)
    on_component_right_click = QtCore.pyqtSignal(AbstractComponent)
    on_component_moved = QtCore.pyqtSignal(AbstractComponent)
    on_right_click = QtCore.pyqtSignal(QPointF)
    on_middle_click = QtCore.pyqtSignal()

    minimum_scale = 0.1

    class DragState(Enum):
        no_drag = auto(),
        drag = auto(),
        drag_component = auto()

    def __init__(self, background: Optional[QPixmap] = None, zoom_speed: float = 0.001, parent=None) -> None:
        super().__init__(parent)
        self._scale: float = 1.0
        self._zoom_speed: float = zoom_speed

        self._start_pos: Optional[QPointF] = None
        self._drag_state: ExtendedScene.DragState = ExtendedScene.DragState.no_drag
        self._current_component: Optional[AbstractComponent] = None

        self._scene: QGraphicsScene = QGraphicsScene()
        self._background = self._scene.addPixmap(background) if background else None
        self.setScene(self._scene)

        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setBackgroundBrush(QBrush(QColor(0, 0, 0)))
        self.setFrameShape(QFrame.NoFrame)

        # Mouse
        self.setMouseTracking(True)

        # For keyboard events
        self.setFocusPolicy(Qt.StrongFocus)

        self._components: List[AbstractComponent] = []

        self._drag_allowed = True

    def clear_scene(self) -> None:
        self._scene.clear()
        self._components = []
        self._background = None
        self.resetTransform()

    def allow_drag(self, allow: bool = True) -> None:
        self._drag_allowed = allow

    def is_drag_allowed(self) -> bool:
        return self._drag_allowed

    def set_background(self, background: QPixmap) -> None:
        if self._background:
            raise ValueError("Call 'clear_scene' first!")
        self._background = self._scene.addPixmap(background)

    def add_component(self, component: AbstractComponent) -> None:
        self._components.append(component)
        self._scene.addItem(component)
        component.update_scale(self._scale)

    def zoom(self, zoom_factor, pos) -> None:  # pos in view coordinates
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

    def move(self, delta):
        # Note: Workaround! See:
        # - https://bugreports.qt.io/browse/QTBUG-7328
        # - https://stackoverflow.com/questions/14610568/how-to-use-the-qgraphicsviews-translate-function
        anchor = self.transformationAnchor()
        self.setTransformationAnchor(QGraphicsView.NoAnchor)  # Override transformation anchor
        self.translate(delta.x(), delta.y())
        self.setTransformationAnchor(anchor)  # Restore old anchor

    def wheelEvent(self, event: QWheelEvent) -> None:
        zoom_factor = 1.0
        zoom_factor += event.angleDelta().y() * self._zoom_speed
        if self._scale * zoom_factor < self.minimum_scale and zoom_factor < 1.0:  # minimum allowed zoom
            return

        self.zoom(zoom_factor, event.pos())
        self._scale *= zoom_factor

        for component in self._components:
            component.update_scale(self._scale)

    def _clicked_item(self, event) -> Optional[AbstractComponent]:
        for item in self.items(event.pos()):
            if isinstance(item, AbstractComponent):
                return item
        return None

    def remove_all_selections(self):
        for item in self._components:
            item.select(False)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        # Check for clicked pin
        item = self._clicked_item(event)

        if event.button() & Qt.LeftButton:
            self._start_pos = self.mapToScene(event.pos())

            if item:
                self.on_component_left_click.emit(item)

                if item.selectable:
                    if item.unique_selection:
                        self.remove_all_selections()
                    item.select(True)

                if item.draggable and self._drag_allowed:
                    self._drag_state = self.DragState.drag_component
                    self._current_component = item
                return

            # We are in drag board mode now
            self._drag_state = self.DragState.drag
            self.setDragMode(QGraphicsView.ScrollHandDrag)

        if event.button() & Qt.RightButton:
            if item:
                self.on_component_right_click.emit(item)
                return

            self.on_right_click.emit(self.mapToScene(event.pos()))

        if event.button() & Qt.MiddleButton:
            self.on_middle_click.emit()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._drag_state == self.DragState.drag:
            delta = self.mapToScene(event.pos()) - self._start_pos
            self.move(delta)
        elif self._drag_state == self.DragState.drag_component:
            self._current_component.setPos(self.mapToScene(event.pos()))

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() & Qt.LeftButton:
            self.setDragMode(QGraphicsView.NoDrag)

            if self._drag_state is self.DragState.drag_component:
                if self._current_component:
                    self.on_component_moved.emit(self._current_component)

            self._drag_state = self.DragState.no_drag

    def resizeEvent(self, event: QResizeEvent) -> None:
        pass

    def all_components(self, class_filter: type = object) -> List[AbstractComponent]:
        """
        Get all components with class class_filter (all components by default).
        :param class_filter:
        :return:
        """

        return list(filter(lambda x: isinstance(x, class_filter), self._components))

    def scale_to_window_size(self, x: float, y: float) -> None:
        """
        Scale to window size.
        For example, if you have window 600x600 and workspace background image 1200x1200, image will be scaled in 4x.
        :param x: window width;
        :param y: window height.
        """

        factor_x = x / self._background.pixmap().width()
        factor_y = y / self._background.pixmap().height()
        factor = max(min(factor_x, factor_y), self.minimum_scale)
        self.resetTransform()
        self._scale = factor
        self.zoom(factor, QPoint(0, 0))
