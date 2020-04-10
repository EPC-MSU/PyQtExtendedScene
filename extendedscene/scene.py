from PyQt5 import QtCore
from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtGui import QBrush, QColor, QPixmap
from PyQt5.QtWidgets import QGraphicsView, QFrame, QGraphicsScene, QGraphicsItem
from typing import Optional, List
from enum import Enum, auto


class AbstractComponent(QGraphicsItem):
    def __init__(self,
                 draggable: bool = True,
                 selectable: bool = True,
                 unique_selection: bool = True):
        """
        Abstract component
        :param draggable: True if component can be dragged
        :param selectable: True if component can be selected
        :param unique_selection: True if selecting this component should reset all others selections
                                 ('selectable' must be set)
        """
        super().__init__()

        self._draggable = draggable
        self._selectable = selectable
        self._unique_selection = unique_selection

    def select(self, selected: bool = True):
        pass

    def update_scale(self, scale: float):
        pass

    @property
    def draggable(self):
        return self._draggable

    @property
    def selectable(self):
        return self._selectable

    @property
    def unique_selection(self):
        return self._unique_selection


class ExtendedScene(QGraphicsView):
    on_component_left_click = QtCore.pyqtSignal(AbstractComponent)
    on_component_right_click = QtCore.pyqtSignal(AbstractComponent)
    on_right_click = QtCore.pyqtSignal(QPointF)
    on_middle_click = QtCore.pyqtSignal()

    class DragState(Enum):
        no_drag = auto(),
        drag = auto(),
        drag_component = auto()

    def __init__(self, image: QPixmap, zoom_speed: float = 0.001, parent=None) -> None:
        super().__init__(parent)

        self._zoom_speed = zoom_speed

        self._start_pos: Optional[QPointF] = None
        self._drag_state: ExtendedScene.DragState = ExtendedScene.DragState.no_drag
        self._current_component: Optional[AbstractComponent] = None

        self._scale: float = 1.0

        scene = QGraphicsScene()
        scene.addPixmap(image)
        self._scene: QGraphicsScene = scene
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

    def add_component(self, component: AbstractComponent):
        self._components.append(component)
        self._scene.addItem(component)
        component.update_scale(self._scale)

    def zoom(self, zoom_factor, pos):  # pos in view coordinates
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

    def wheelEvent(self, event):
        zoom_factor = 1.0
        zoom_factor += event.angleDelta().y() * self._zoom_speed
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

    def mousePressEvent(self, event):
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

                if item.draggable:
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

    def mouseMoveEvent(self, event):
        if self._drag_state == self.DragState.drag:
            delta = self.mapToScene(event.pos()) - self._start_pos
            self.move(delta)
        elif self._drag_state == self.DragState.drag_component:
            self._current_component.setPos(self.mapToScene(event.pos()))

    def mouseReleaseEvent(self, event):
        if event.button() & Qt.LeftButton:
            self.setDragMode(QGraphicsView.NoDrag)
            self._drag_state = self.DragState.no_drag

    def all_components(self, class_filter: type = object) -> List[AbstractComponent]:
        """
        Get all components with class class_filter (all components by default)
        :param class_filter:
        :return:
        """
        return list(filter(lambda x: isinstance(x, class_filter), self._components))
