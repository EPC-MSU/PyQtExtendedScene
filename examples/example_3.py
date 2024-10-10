import os
import sys
from PyQt5.QtCore import pyqtSlot, QRectF
from PyQt5.QtGui import QBrush, QColor, QPixmap
from PyQt5.QtWidgets import QDialog, QApplication, QHBoxLayout, QRadioButton, QVBoxLayout


try:
    from PyQtExtendedScene import ComponentGroup, ExtendedScene, PointComponent, RectComponent
    from PyQtExtendedScene.scenemode import SceneMode
except ImportError:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from PyQtExtendedScene import ComponentGroup, ExtendedScene, PointComponent, RectComponent
    from PyQtExtendedScene.scenemode import SceneMode


class Dialog(QDialog):

    def __init__(self) -> None:
        super().__init__()
        self._init_ui()

    @staticmethod
    def _create_extended_scene() -> ExtendedScene:
        # Open workspace background image
        path_to_image = os.path.join("images", "workspace.png")
        if os.path.isfile(path_to_image):
            image = QPixmap(path_to_image)
            image = image.scaled(800, 600)
        else:
            image = None

        widget = ExtendedScene(image)
        widget.setBackgroundBrush(QBrush(QColor("white")))

        point_component = PointComponent(4, draggable=False, selectable=True)
        point_component.setBrush(QBrush(QColor("red")))
        point_component.setPos(100, 300)
        widget.add_component(point_component)

        rect_component = RectComponent(QRectF(0, 0, 100, 150), draggable=False, selectable=True)
        rect_component.setPos(100, 100)
        rect_component.setBrush(QBrush(QColor("red")))
        widget.add_component(rect_component)

        point_component_for_group = PointComponent(4)
        point_component_for_group.setBrush(QBrush(QColor("green")))
        point_component_for_group.setPos(400, 300)
        # widget.add_component(point_component_for_group)

        rect_component_for_group = RectComponent(QRectF(0, 0, 200, 100))
        rect_component_for_group.setBrush(QBrush(QColor("green")))
        rect_component_for_group.setPos(400, 100)
        # widget.add_component(rect_component_for_group)

        group = ComponentGroup()
        group.addToGroup(point_component_for_group)
        group.addToGroup(rect_component_for_group)
        widget.add_component(group)
        return widget

    def _init_ui(self) -> None:
        self.extended_scene = self._create_extended_scene()

        self.button_no_action = QRadioButton("Обычный режим")
        self.button_no_action.setChecked(True)
        self.button_no_action.toggled.connect(self._set_mode)
        self.button_edit = QRadioButton("Редактирование")
        self.button_edit.toggled.connect(self._set_mode)
        self.button_edit_group = QRadioButton("Редактирование составного компонента")
        self.button_edit_group.toggled.connect(self._set_mode)
        h_layout = QHBoxLayout()
        h_layout.addWidget(self.button_no_action)
        h_layout.addWidget(self.button_edit)
        h_layout.addWidget(self.button_edit_group)

        layout = QVBoxLayout()
        layout.addLayout(h_layout)
        layout.addWidget(self.extended_scene)
        self.setLayout(layout)

    @pyqtSlot()
    def _set_mode(self) -> None:
        if self.sender() == self.button_edit:
            mode = SceneMode.EDIT
        elif self.sender() == self.button_edit_group:
            mode = SceneMode.EDIT_GROUP
        else:
            mode = SceneMode.NO_ACTION
        self.extended_scene.set_scene_mode(mode)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    dialog = Dialog()
    dialog.show()
    sys.exit(app.exec_())
