import os
import sys
from PyQt5.QtCore import QPointF, QRectF
from PyQt5.QtGui import QBrush, QColor, QPixmap
from PyQt5.QtWidgets import QApplication, QFileDialog, QGraphicsEllipseItem
from PyQtExtendedScene import AbstractComponent, ExtendedScene


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

    # Open workspace background image
    path_to_image = os.path.join("images", "workspace.png")
    if not os.path.isfile(path_to_image):
        path_to_image = QFileDialog().getOpenFileName(caption="Open workspace image",
                                                      filter="Image Files (*.png *.jpg *.bmp *.tiff)")[0]

    image = QPixmap(path_to_image)
    image = image.scaled(800, 600)
    # Create workspace!
    widget = ExtendedScene(image)

    # Let's add some components to our workspace
    widget.add_component(MyComponent(10, 10, "My component 1"))
    widget.add_component(MyComponent(100, 200, "My component 2"))

    # Handle left click
    widget.on_component_left_click.connect(left_click)
    widget.show()

    sys.exit(app.exec_())
