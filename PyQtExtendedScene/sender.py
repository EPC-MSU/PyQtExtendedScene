from typing import Any, Callable
from PyQt5.QtCore import pyqtSignal, QObject


def get_signal_sender(value_type: type) -> type:
    """
    :param value_type: the type of values that the signal will need to send.
    :return: class that sends values of a given type.
    """

    class Sender(QObject):

        _signal: pyqtSignal = pyqtSignal(value_type)

        def connect(self, func: Callable[..., Any]) -> None:
            """
            :param func: callback function that should receive values when sent via a signal.
            """

            self._signal.connect(func)

        def emit(self, value) -> None:
            """
            :param value: value to send.
            """

            self._signal.emit(value)

    return Sender
