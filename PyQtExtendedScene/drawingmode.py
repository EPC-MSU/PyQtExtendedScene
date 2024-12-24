from enum import auto, Enum


class DrawingMode(Enum):
    """
    Enumerating of drawing modes: only on the background, or everywhere at all.
    """

    EVERYWHERE = auto()
    ONLY_IN_BACKGROUND = auto()
