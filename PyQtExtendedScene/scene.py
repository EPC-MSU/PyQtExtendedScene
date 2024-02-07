from enum import auto, Enum
from typing import List, Optional
from PyQt5.QtCore import pyqtSignal, QPoint, QPointF, QRectF, Qt
from PyQt5.QtGui import QBrush, QColor, QMouseEvent, QPainter, QPixmap, QResizeEvent, QWheelEvent
from PyQt5.QtWidgets import QFrame, QGraphicsItem, QGraphicsPixmapItem, QGraphicsScene, QGraphicsView, QWidget


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
    def unique_selection(self) -> bool:
        """
        :return: True if selecting this component should reset all others selections.
        """

        return self._unique_selection

    def boundingRect(self) -> QRectF:
        """
        :return: the outer bounds of the component as a rectangle.
        """

        # By default bounding rect of our object is a bounding rect of children items
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

        pass

    def update_scale(self, scale: float) -> None:
        """
        :param scale: new scale factor for component.
        """

        pass


class ExtendedScene(QGraphicsView):

    on_component_left_click = pyqtSignal(AbstractComponent)
    on_component_right_click = pyqtSignal(AbstractComponent)
    on_component_moved = pyqtSignal(AbstractComponent)
    on_right_click = pyqtSignal(QPointF)
    on_middle_click = pyqtSignal()

    minimum_scale = 0.1

    class DragState(Enum):
        no_drag = auto()
        drag = auto()
        drag_component = auto()

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
        self._drag_state: ExtendedScene.DragState = ExtendedScene.DragState.no_drag
        self._start_pos: Optional[QPointF] = None

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

    def _clicked_item(self, event: QMouseEvent) -> Optional[AbstractComponent]:
        """
        :param event: mouse event.
        :return: a component that is located at the point specified by the mouse.
        """

        for item in self.items(event.pos()):
            if isinstance(item, AbstractComponent):
                return item
        return None

    def add_component(self, component: AbstractComponent) -> None:
        """
        :param component: component to be added to the scene.
        """

        self._components.append(component)
        self._scene.addItem(component)
        component.update_scale(self._scale)

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

        if self._drag_state == self.DragState.drag:
            delta = self.mapToScene(event.pos()) - self._start_pos
            self.move(delta)
        elif self._drag_state == self.DragState.drag_component:
            self._current_component.setPos(self.mapToScene(event.pos()))

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """
        :param event: mouse event.
        """

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

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """
        :param event: mouse event.
        """

        if event.button() & Qt.LeftButton:
            self.setDragMode(QGraphicsView.NoDrag)

            if self._drag_state is self.DragState.drag_component:
                if self._current_component:
                    self.on_component_moved.emit(self._current_component)

            self._drag_state = self.DragState.no_drag

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
        factor = max(min(factor_x, factor_y), self.minimum_scale)
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
        if self._scale * zoom_factor < self.minimum_scale and zoom_factor < 1.0:  # minimum allowed zoom
            return

        self.zoom(zoom_factor, event.pos())
        self._scale *= zoom_factor

        for component in self._components:
            component.update_scale(self._scale)

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
