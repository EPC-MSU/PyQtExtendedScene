import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PyQt5.QtCore import QPointF, QRectF
from PyQt5.QtGui import QBrush, QColor
from PyQt5.QtWidgets import QApplication
from PyQtExtendedScene import ExtendedScene, ScalableComponent


if __name__ == "__main__":
    app = QApplication(sys.argv)
    # Create workspace!
    widget = ExtendedScene()
    widget.setBackgroundBrush(QBrush(QColor("white")))

    n = 20
    m = 20
    width = 50
    height = 50
    dx = 5
    dy = 5
    for i in range(n):
        for j in range(m):
            x = j * (width + dx)
            y = i * (height + dy)
            component = ScalableComponent(QRectF(0, 0, width, height))
            component.setPos(x, y)
            widget.add_component(component)

    widget._scene.setSceneRect(QRectF(QPointF(-500, -500), QPointF(1500, 1500)))

    widget.show()
    sys.exit(app.exec_())
