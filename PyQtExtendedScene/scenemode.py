from enum import auto, Enum


class SceneMode(Enum):
    """
    Enumeration of scene modes.
    """

    EDIT = auto()
    EDIT_GROUP = auto()
    NO_ACTION = auto()
