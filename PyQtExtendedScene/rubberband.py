from enum import auto, Enum
from PyQt5.QtCore import QRectF
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QGraphicsRectItem
from . import utils as ut
from .rectcomponent import RectComponent


class RubberBand(RectComponent):
    """
    Class for displaying rubber band after the right mouse button is released.
    """

    PEN_COLOR: QColor = QColor(0, 120, 255)
    Z_VALUE: float = 2

    class DisplayMode(Enum):
        """
        Class with a list of rubber band display modes when selected with the mouse.
        """

        HIDE = auto()  # hide the rubber band after the left mouse button is released
        SHOW = auto()  # leave the rubber band shown after the left mouse button is released

    def __init__(self) -> None:
        super().__init__(draggable=False, selectable=False)
        self._display_mode: RubberBand.DisplayMode = RubberBand.DisplayMode.HIDE
        self._should_limit_size_to_background: bool = False
        self.hide()

    def _limit_size_to_background(self) -> None:
        if not hasattr(self.scene(), "background"):
            return

        rect = self.mapRectToScene(self.rect())
        background_rect = self.scene().background.sceneBoundingRect()
        if not rect or not background_rect:
            return

        if (background_rect.right() < rect.left() or rect.right() < background_rect.left() or
                background_rect.bottom() < rect.top() or rect.bottom() < background_rect.top()):
            self.setRect(QRectF())
        else:
            left = max(rect.left(), background_rect.left())
            right = min(rect.right(), background_rect.right())
            top = max(rect.top(), background_rect.top())
            bottom = min(rect.bottom(), background_rect.bottom())
            self.setRect(QRectF(left, top, right - left, bottom - top))

    def limit_size_to_background(self, limit: bool) -> None:
        """
        :param limit: if True, then it is needed to limit the size of the rubber band within the background.
        """

        self._should_limit_size_to_background = limit

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
            if self._should_limit_size_to_background:
                self._limit_size_to_background()
            self.setVisible(self._display_mode is RubberBand.DisplayMode.SHOW)

    def update_selection(self) -> None:
        QGraphicsRectItem.setPen(self, ut.get_dashed_pen(self._solid_pen))
