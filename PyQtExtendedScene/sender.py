from PyQt5.QtCore import pyqtSignal, QObject


class Sender(QObject):

    signal: pyqtSignal = pyqtSignal(bool)

    def connect(self, func) -> None:
        self.signal.connect(func)

    def emit(self, value: bool) -> None:
        self.signal.emit(value)
