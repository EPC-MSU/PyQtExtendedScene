import os
import sys
from PyQt5.QtCore import QPointF, QRectF
from PyQt5.QtGui import QBrush, QColor
from PyQt5.QtWidgets import QApplication


try:
    from PyQtExtendedScene import ExtendedScene, PointComponent, ScalableComponent
except ImportError:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from PyQtExtendedScene import ExtendedScene, PointComponent, ScalableComponent


if __name__ == "__main__":
    app = QApplication(sys.argv)
    # Create workspace!
    widget = ExtendedScene()
    widget.setBackgroundBrush(QBrush(QColor("white")))

    point_component = PointComponent(4, 8)
    point_component.setBrush(QBrush(QColor("red")))
    point_component.setPos(100, 300)
    widget.add_component(point_component)

    rect_component = ScalableComponent(QRectF(0, 0, 100, 150))
    rect_component.setBrush(QBrush(QColor("green")))
    widget.add_component(rect_component)

    widget._scene.setSceneRect(QRectF(QPointF(-500, -500), QPointF(1500, 1500)))

    widget.show()
    sys.exit(app.exec_())