from enum import auto, Enum


class SceneMode(Enum):
    """
    Enumeration of scene modes.
    """

    EDIT = auto()  # individual component editing mode
    EDIT_GROUP = auto()  # group component editing mode
    NORMAL = auto()  # normal mode
