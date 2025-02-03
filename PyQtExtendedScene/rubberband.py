from enum import auto, Enum
from typing import Optional
from PyQt5.QtCore import QRectF
from PyQt5.QtGui import QColor, QPen, QBrush
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

    def __init__(self, pen: Optional[QPen] = None) -> None:
        """
        :param pen: pen for rubber band.
        """

        super().__init__(pen=pen, draggable=False, selectable=False)
        self._display_mode: RubberBand.DisplayMode = RubberBand.DisplayMode.HIDE
        self._should_limit_size_to_background: bool = False
        self.hide()

    def _limit_size_to_background(self, rect: QRectF) -> None:
        """
        :param rect: new rectangle for rubber band.
        """

        if not hasattr(self.scene(), "background") or self.scene().background is None:
            return

        rect = self.mapRectToScene(rect)
        background_rect = self.scene().background.sceneBoundingRect()
        limit_rect = ut.fit_rect_to_background(background_rect, rect)
        if not limit_rect:
            self.setRect(QRectF())
        else:
            self.setRect(limit_rect)

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

    def set_parameters(self, pen: Optional[QPen] = None, brush: Optional[QBrush] = None) -> None:
        """
        :param pen: pen for component;
        :param brush: brush for component.
        """

        super().set_parameters(pen=pen, brush=brush)
        self._update_pen_for_selection = ut.get_function_to_update_dashed_pen(self._pen)

    def set_rect(self, rect: QRectF) -> bool:
        """
        :param rect: new rectangle for rubber band.
        :return: True if the rubber band geometry has been changed, otherwise False.
        """

        if rect.height() and rect.width():
            if self._should_limit_size_to_background:
                self._limit_size_to_background(rect)
            else:
                self.setRect(rect)
            self.setVisible(self._display_mode is RubberBand.DisplayMode.SHOW)
            return True

        return False

    def update_selection(self) -> None:
        QGraphicsRectItem.setPen(self, self._update_pen_for_selection())
