from PyQt5.QtWidgets import QGraphicsEllipseItem
from PyQt5.QtCore import QRectF, QPointF
from PyQt5.QtGui import QBrush, QColor
from extendedscene import ExtendedScene, AbstractComponent


class MyComponent(AbstractComponent):

    selected_size = 20
    normal_size = 10

    def __init__(self, x: float, y: float, descr: str = ""):
        super().__init__(draggable=True, selectable=True, unique_selection=True)
        self._r = self.normal_size

        self.setPos(QPointF(x, y))

        self._item = QGraphicsEllipseItem(-self._r, -self._r, self._r * 2, self._r * 2, self)
        self._item.setBrush(QBrush(QColor(0xFFFF00)))

        self.redraw()

        self._descr = descr

    def redraw(self):
        self._item.setRect(QRectF(-self._r, -self._r, self._r * 2, self._r * 2))

    def select(self, selected: bool = True):
        self._r = self.selected_size if selected else self.normal_size
        self.redraw()

    def boundingRect(self):
        return self.childrenBoundingRect()

    @property
    def description(self):
        return self._descr


if __name__ == '__main__':
    import sys
    from os.path import isfile
    from PyQt5.QtWidgets import QFileDialog, QApplication
    from PyQt5.QtGui import QPixmap

    app = QApplication(sys.argv)

    path_to_image = "workspace.png"
    if not isfile(path_to_image):
        path_to_image = QFileDialog().getOpenFileName(caption="Open workspace image",
                                                      filter="Image Files (*.png *.jpg *.bmp *.tiff)")[0]

    image = QPixmap(path_to_image)
    image = image.scaled(800, 600)
    widget = ExtendedScene(image)

    widget.add_component(MyComponent(10, 10, "My component 1"))
    widget.add_component(MyComponent(100, 200, "My component 2"))

    def left_click(component):
        if isinstance(component, MyComponent):
            print(f"Left click on '{component.description}'")

    widget.on_component_left_click.connect(left_click)

    widget.show()

    sys.exit(app.exec_())
