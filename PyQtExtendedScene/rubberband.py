from enum import auto, Enum
from PyQt5.QtCore import QRectF
from PyQt5.QtWidgets import QGraphicsRectItem
from . import utils as ut
from .rectcomponent import RectComponent


class RubberBand(RectComponent):
    """
    Class for displaying rubber band after the right mouse button is released.
    """

    class DisplayMode(Enum):
        """
        Class with a list of rubber band display modes when selected with the mouse.
        """

        HIDE = auto()  # hide the rubber band after the left mouse button is released
        SHOW = auto()  # leave the rubber band shown after the left mouse button is released

    def __init__(self) -> None:
        super().__init__(draggable=False, selectable=False)
        self._display_mode: RubberBand.DisplayMode = RubberBand.DisplayMode.HIDE
        self.hide()

    def set_display_mode(self, mode: "RubberBand.DisplayMode") -> None:
        """
        :param mode: new display mode.
        """

        self._display_mode = mode

    def set_rect(self, rect: QRectF) -> None:
        """
        :param rect: new rectangle for rubber band.
        """

        if rect.height() and rect.width():
            self.setRect(rect)
            self.setVisible(self._display_mode is RubberBand.DisplayMode.SHOW)

    def update_selection(self) -> None:
        QGraphicsRectItem.setPen(self, ut.get_dashed_pen(self._solid_pen))
