import os
import sys
import unittest
from typing import List
from PyQt6.QtCore import QPointF, QRectF
from PyQt6.QtGui import QBrush, QColor, QPixmap
from PyQt6.QtWidgets import QApplication, QGraphicsEllipseItem
from PyQtExtendedScene import AbstractComponent, ExtendedScene


class SimpleComponent(AbstractComponent):

    NORMAL_SIZE: float = 10
    SELECTED_SIZE: float = 20

    def __init__(self, x: float, y: float, description: str = "") -> None:
        """
        :param x: horizontal coordinate for the component;
        :param y: vertical coordinate for the component;
        :param description: some description for the component.
        """

        super().__init__(draggable=True, selectable=True, unique_selection=True)
        self._description: str = description
        self._r: float = SimpleComponent.NORMAL_SIZE
        self.setPos(QPointF(x, y))
        self._item = QGraphicsEllipseItem(-self._r, -self._r, self._r * 2, self._r * 2, self)
        self._item.setBrush(QBrush(QColor(0xFFFF00)))

    @property
    def description(self) -> str:
        """
        :return: description for the component.
        """

        return self._description

    def select(self, selected: bool = True) -> None:
        self._r = SimpleComponent.SELECTED_SIZE if selected else SimpleComponent.NORMAL_SIZE
        self._item.setRect(QRectF(-self._r, -self._r, self._r * 2, self._r * 2))


class OtherComponent(AbstractComponent):
    pass


class TestExtendedScene(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls._app: QApplication = QApplication(sys.argv)

    def setUp(self) -> None:
        path = os.path.join(os.path.dirname(__file__), "data", "background_1.png")
        background = QPixmap(path)
        self.scene: ExtendedScene = ExtendedScene(background)

        self.simple_components: List[SimpleComponent] = []
        for i in range(5):
            component = SimpleComponent(i, i, f"simple component {i}")
            self.scene.add_component(component)
            self.simple_components.append(component)

        self.other_components: List[OtherComponent] = []
        for i in range(7):
            component = OtherComponent()
            self.scene.add_component(component)
            self.other_components.append(component)

    def test_add_component_and_all_components(self) -> None:
        self.assertEqual(len(self.scene.all_components()), 12)

        simple_components_from_scene = self.scene.all_components(SimpleComponent)
        self.assertEqual(len(simple_components_from_scene), 5)
        for i, component in enumerate(simple_components_from_scene):
            self.assertEqual(component, self.simple_components[i])

        other_components_from_scene = self.scene.all_components(OtherComponent)
        self.assertEqual(len(other_components_from_scene), 7)
        for i, component in enumerate(other_components_from_scene):
            self.assertEqual(component, self.other_components[i])

    def test_allow_drag_and_is_drag_allowed(self) -> None:
        scene = ExtendedScene()
        self.assertTrue(scene.is_drag_allowed())

        scene.allow_drag(False)
        self.assertFalse(scene.is_drag_allowed())

    def test_clear_scene(self) -> None:
        self.assertEqual(len(self.scene.all_components()), 12)
        self.assertIsNotNone(self.scene._background)

        self.scene.clear_scene()
        self.assertEqual(len(self.scene.all_components()), 0)
        self.assertIsNone(self.scene._background)

    def test_set_background(self) -> None:
        path = os.path.join(os.path.dirname(__file__), "data", "background_2.png")
        background = QPixmap(path)

        with self.assertRaises(ValueError):
            self.scene.set_background(background)

        self.scene.clear_scene()
        self.scene.set_background(background)
        self.assertIsNotNone(self.scene._background)
