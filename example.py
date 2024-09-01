import os
import sys
from PyQt5.QtCore import QPointF, QRectF
from PyQt5.QtGui import QBrush, QColor, QPixmap
from PyQt5.QtWidgets import QApplication, QFileDialog, QGraphicsEllipseItem
from PyQtExtendedScene import AbstractComponent, ExtendedScene, ScalableComponent


# Let's describe our own component
class MyComponent(AbstractComponent):

    normal_size = 10
    selected_size = 20

    def __init__(self, x: float, y: float, description: str = "") -> None:
        """
        :param x: horizontal coordinate for the component;
        :param y: vertical coordinate for the component;
        :param description: some description for the component.
        """

        super().__init__(draggable=True, selectable=True, unique_selection=True)
        # Add description to our object - it will be used in "click" callback function
        self._descr: str = description
        self._r: float = self.normal_size

        self.setPos(QPointF(x, y))

        # We must describe how to draw our own component. Our own component will be just a circle
        self._item = QGraphicsEllipseItem(-self._r, -self._r, self._r * 2, self._r * 2, self)
        # ... yellow circle
        self._item.setBrush(QBrush(QColor(0xFFFF00)))

    @property
    # That is our own property
    def description(self) -> str:
        """
        :return: description for the component.
        """

        return self._descr

    # We must override parent method "select" because our component changes shape when selected
    def select(self, selected: bool = True) -> None:
        # Radius of our circle changes when selected
        self._r = self.selected_size if selected else self.normal_size
        # redraw our object with new radius
        self._item.setRect(QRectF(-self._r, -self._r, self._r * 2, self._r * 2))


def left_click(component: MyComponent) -> None:
    if isinstance(component, MyComponent):
        print(f"Left click on '{component.description}'")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    # Create workspace!
    widget = ExtendedScene()
    widget.setBackgroundBrush(QBrush(QColor("white")))

    n = 10
    m = 10
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

    # Handle left click
    widget.on_component_left_click.connect(left_click)
    widget.show()

    sys.exit(app.exec_())
