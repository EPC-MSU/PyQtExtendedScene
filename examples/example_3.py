import os
import sys
from PyQt5.QtCore import QPointF, QRectF
from PyQt5.QtGui import QBrush, QColor
from PyQt5.QtWidgets import QApplication


try:
    from PyQtExtendedScene import ExtendedScene, PointComponent
except ImportError:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from PyQtExtendedScene import ExtendedScene, PointComponent


if __name__ == "__main__":
    app = QApplication(sys.argv)
    # Create workspace!
    widget = ExtendedScene()
    widget.setBackgroundBrush(QBrush(QColor("white")))

    component = PointComponent(4, 8)
    component.setBrush(QBrush(QColor("red")))
    component.setPos(100, 300)
    widget.add_component(component)

    widget._scene.setSceneRect(QRectF(QPointF(-500, -500), QPointF(1500, 1500)))

    widget.show()
    sys.exit(app.exec_())
