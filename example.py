from PyQt5.QtWidgets import QGraphicsEllipseItem
from PyQt5.QtCore import QRectF, QPointF
from PyQt5.QtGui import QBrush, QColor
from PyQtExtendedScene import ExtendedScene, AbstractComponent


# Let's describe our own component
class MyComponent(AbstractComponent):
    selected_size = 20
    normal_size = 10

    def __init__(self, x: float, y: float, descr: str = ""):
        super().__init__(draggable=True, selectable=True, unique_selection=True)
        self._r = self.normal_size

        self.setPos(QPointF(x, y))

        # Our own component will be just a circle
        self._item = QGraphicsEllipseItem(-self._r, -self._r, self._r * 2, self._r * 2, self)
        # .. yellow circle
        self._item.setBrush(QBrush(QColor(0xFFFF00)))

        # Add description to our object - it will be used in "click" callback function
        self._descr = descr

    def select(self, selected: bool = True):
        # Radius of our circle changes when selected
        self._r = self.selected_size if selected else self.normal_size
        # redraw our object with new radius
        self._item.setRect(QRectF(-self._r, -self._r, self._r * 2, self._r * 2))

    def boundingRect(self):
        # Bounding rect of our object is a bounding rect of children item (e.g. circle)
        return self.childrenBoundingRect()

    @property
    def description(self):
        # Our own field
        return self._descr


if __name__ == '__main__':
    import sys
    from os.path import isfile
    from PyQt5.QtWidgets import QFileDialog, QApplication
    from PyQt5.QtGui import QPixmap

    app = QApplication(sys.argv)

    # Open workspace background image
    path_to_image = "workspace.png"
    if not isfile(path_to_image):
        path_to_image = QFileDialog().getOpenFileName(caption="Open workspace image",
                                                      filter="Image Files (*.png *.jpg *.bmp *.tiff)")[0]

    image = QPixmap(path_to_image)
    image = image.scaled(800, 600)
    widget = ExtendedScene(image)

    # Let's add some components to our workspace
    widget.add_component(MyComponent(10, 10, "My component 1"))
    widget.add_component(MyComponent(100, 200, "My component 2"))


    def left_click(component):
        if isinstance(component, MyComponent):
            print(f"Left click on '{component.description}'")


    # Handle left click
    widget.on_component_left_click.connect(left_click)

    widget.show()

    sys.exit(app.exec_())
