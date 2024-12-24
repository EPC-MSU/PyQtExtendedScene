import logging


def set_logger(level: int = logging.INFO) -> None:
    """
    :param level: logging level.
    """

    formatter = logging.Formatter("[%(asctime)s %(levelname)s] %(message)s")
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    stream_handler.setLevel(level)

    logger = logging.getLogger("pyqtextendedscene")
    logger.addHandler(stream_handler)
    logger.setLevel(level)
    logger.propagate = False
