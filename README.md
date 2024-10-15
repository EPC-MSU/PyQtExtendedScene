# PyQtExtendedScene

PyQtExtendedScene is a little library for creating workspaces.

Having described the method of drawing your components, with this library you get (draggable) workspace (scene) where the components you described can be selected, moved, deleted, etc. The scene itself can be increased, reduced, the work area may be moved.

Repository: https://github.com/EPC-MSU/PyQtExtendedScene

## Installation

Installation is very simple:
```bash
pip install PyQtExtendedScene
```

## Working example

```Python
import os
import sys
from PyQt5.QtGui import QBrush, QColor, QPixmap
from PyQt5.QtWidgets import QApplication
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

        super().__init__(MyComponent.NORMAL_SIZE, draggable=True, selectable=True)
        # Add description to our object - it will be used in "click" callback function
        self._descr: str = description
        # ... yellow circle
        self.setBrush(QBrush(QColor(0xFFFF00)))
        self.setPos(x, y)

    @property
    def description(self) -> str:
        """
        That is our own property.
        :return: description for the component.
        """

        return self._descr


def left_click(component: MyComponent) -> None:
    if isinstance(component, MyComponent):
        print(f"Left click on '{component.description}'")


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
    widget.on_component_left_click.connect(left_click)
    widget.show()

    sys.exit(app.exec_())

```
Workspace example:

![Workspace example](https://i.imgur.com/DWi0tkN.gif)
