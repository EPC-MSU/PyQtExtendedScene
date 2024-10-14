import os
import sys
from PyQt5.QtCore import pyqtSlot, QRectF
from PyQt5.QtGui import QBrush, QColor
from PyQt5.QtWidgets import QApplication, QDialog, QHBoxLayout, QRadioButton, QVBoxLayout


try:
    from PyQtExtendedScene import ExtendedScene, RectComponent, SceneMode
except ImportError:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from PyQtExtendedScene import ExtendedScene, RectComponent, SceneMode


class Dialog(QDialog):

    HEIGHT: int = 800
    WIDTH: int = 800

    def __init__(self) -> None:
        super().__init__()
        self._init_ui()

    @staticmethod
    def _create_extended_scene() -> ExtendedScene:
        widget = ExtendedScene()
        widget.setBackgroundBrush(QBrush(QColor("white")))
        widget.scene().setSceneRect(QRectF(-50 * 50, -50 * 50, 2 * 50 * 50, 2 * 50 * 50))
        return widget

    def _create_rectangles_on_scene(self) -> None:
        n = 20
        m = 20
        width, height = 40, 40
        dx, dy = 5, 5
        for i in range(n):
            for j in range(m):
                x = j * (width + dx)
                y = i * (height + dy)
                component = RectComponent(QRectF(0, 0, width, height))
                component.setPos(x, y)
                self.extended_scene.add_component(component)

    def _init_ui(self) -> None:
        self.resize(Dialog.WIDTH, Dialog.HEIGHT)

        self.extended_scene = self._create_extended_scene()
        self._create_rectangles_on_scene()

        self.button_no_action = QRadioButton("Обычный режим")
        self.button_no_action.setChecked(True)
        self.button_no_action.toggled.connect(self._set_mode)
        self.button_edit = QRadioButton("Режим редактирования")
        self.button_edit.toggled.connect(self._set_mode)

        h_layout = QHBoxLayout()
        h_layout.setContentsMargins(5, 5, 5, 5)
        h_layout.addWidget(self.button_no_action)
        h_layout.addWidget(self.button_edit)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addLayout(h_layout)
        layout.addWidget(self.extended_scene)
        self.setLayout(layout)

    @pyqtSlot()
    def _set_mode(self) -> None:
        if self.sender() == self.button_edit:
            mode = SceneMode.EDIT
        else:
            mode = SceneMode.NORMAL
        self.extended_scene.set_scene_mode(mode)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    dialog = Dialog()
    dialog.show()
    sys.exit(app.exec_())
