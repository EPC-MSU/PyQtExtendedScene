import os
import sys
from PyQt5.QtGui import QBrush, QColor, QPixmap
from PyQt5.QtWidgets import QApplication


try:
    from PyQtExtendedScene import ExtendedScene, PointComponent
except ImportError:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from PyQtExtendedScene import ExtendedScene, PointComponent


# Let's describe our own component
class MyComponent(PointComponent):

    NORMAL_SIZE: float = 10

    def __init__(self, x: float, y: float, description: str = "") -> None:
        """
        :param x: horizontal coordinate for the component;
        :param y: vertical coordinate for the component;
        :param description: some description for the component.
        """

        super().__init__(MyComponent.NORMAL_SIZE, brush=QBrush(QColor(0xFFFF00)), draggable=True, selectable=True)
        # Add description to our object - it will be used in "click" callback function
        self._descr: str = description
        self.setPos(x, y)

    @property
    def description(self) -> str:
        """
        That is our own property.
        :return: description for the component.
        """

        return self._descr


def handle_component_move(component: MyComponent) -> None:
    if isinstance(component, MyComponent):
        print(f"Move '{component.description}'")


def handle_left_click(component: MyComponent) -> None:
    if isinstance(component, MyComponent):
        print(f"Left click on '{component.description}'")


def handle_right_click(component: MyComponent) -> None:
    if isinstance(component, MyComponent):
        print(f"Right click on '{component.description}'")


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Open workspace background image
    path_to_image = os.path.join("images", "workspace.png")
    image = QPixmap(path_to_image)
    image = image.scaled(800, 600)
    # Create workspace
    widget = ExtendedScene(image)

    # Let's add some components to our workspace
    widget.add_component(MyComponent(500, 400, "My component 1"))
    widget.add_component(MyComponent(100, 200, "My component 2"))

    # Handle left click
    widget.on_component_left_click.connect(handle_left_click)
    widget.component_moved.connect(handle_component_move)
    widget.on_component_right_click.connect(handle_right_click)
    widget.fit_in_view()
    widget.show()

    sys.exit(app.exec_())
