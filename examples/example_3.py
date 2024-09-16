import os
import sys
from PyQt5.QtCore import QRectF
from PyQt5.QtGui import QBrush, QColor, QPixmap
from PyQt5.QtWidgets import QApplication


try:
    from PyQtExtendedScene import ComponentGroup, ExtendedScene, PointComponent, ScalableComponent
    from PyQtExtendedScene.scenemode import SceneMode
except ImportError:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from PyQtExtendedScene import ComponentGroup, ExtendedScene, PointComponent, ScalableComponent
    from PyQtExtendedScene.scenemode import SceneMode


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
    widget = ExtendedScene(image)
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

    widget.set_scene_mode(SceneMode.NO_ACTION)

    widget.show()
    sys.exit(app.exec_())
