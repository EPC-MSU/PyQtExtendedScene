import os
import sys
from PyQt5.QtCore import pyqtSlot, QPointF, QRectF
from PyQt5.QtGui import QBrush, QColor, QPixmap
from PyQt5.QtWidgets import QAction, QApplication, QMenu


try:
    from PyQtExtendedScene import ComponentGroup, ExtendedScene, PointComponent, ScalableComponent
    from PyQtExtendedScene.scenemode import SceneMode
except ImportError:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from PyQtExtendedScene import ComponentGroup, ExtendedScene, PointComponent, ScalableComponent
    from PyQtExtendedScene.scenemode import SceneMode


class SceneWithMenu(ExtendedScene):

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.middle_clicked.connect(self._show_context_menu)

    @pyqtSlot(QPointF)
    def _show_context_menu(self, pos: QPointF) -> None:
        no_action = QAction("Обычный режим")
        no_action.triggered.connect(lambda: self.set_scene_mode(SceneMode.NO_ACTION))
        edit_action = QAction("Режим редактирования")
        edit_action.triggered.connect(lambda: self.set_scene_mode(SceneMode.EDIT))
        edit_group_action = QAction("Режим редактирования группы")
        edit_group_action.triggered.connect(lambda: self.set_scene_mode(SceneMode.EDIT_GROUP))

        menu = QMenu(self)
        menu.addAction(no_action)
        menu.addAction(edit_action)
        menu.addAction(edit_group_action)

        from_scene = self.mapFromScene(pos)
        menu.exec_(self.mapToGlobal(from_scene))


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Open workspace background image
    path_to_image = os.path.join("images", "workspace.png")
    if os.path.isfile(path_to_image):
        image = QPixmap(path_to_image)
        image = image.scaled(800, 600)
    else:
        image = None

    # Create workspace!
    widget = SceneWithMenu(image)
    widget.setBackgroundBrush(QBrush(QColor("white")))

    point_component = PointComponent(4)
    point_component.setBrush(QBrush(QColor("red")))
    point_component.setPos(100, 300)
    widget.add_component(point_component)

    rect_component = ScalableComponent(QRectF(0, 0, 100, 150))
    rect_component.setPos(100, 100)
    rect_component.setBrush(QBrush(QColor("red")))
    widget.add_component(rect_component)

    point_component_for_group = PointComponent(4)
    point_component_for_group.setBrush(QBrush(QColor("green")))
    point_component_for_group.setPos(400, 300)

    rect_component_for_group = ScalableComponent(QRectF(0, 0, 200, 100))
    rect_component_for_group.setBrush(QBrush(QColor("green")))
    rect_component_for_group.setPos(400, 100)

    group = ComponentGroup()
    group.addToGroup(point_component_for_group)
    group.addToGroup(rect_component_for_group)
    widget.add_component(group)

    widget.show()
    sys.exit(app.exec_())
