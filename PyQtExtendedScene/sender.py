from PyQt5.QtCore import pyqtSignal, QObject


def get_signal_sender(value_type: type):
    """
    :param value_type:
    """

    class Sender(QObject):

        _signal: pyqtSignal = pyqtSignal(value_type)

        def connect(self, func) -> None:
            self._signal.connect(func)

        def emit(self, value) -> None:
            self._signal.emit(value)

    return Sender
