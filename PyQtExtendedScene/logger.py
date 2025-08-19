import logging


def set_logger(name: str, level: int = logging.INFO) -> None:
    """
    :param name: logger name;
    :param level: logging level.
    """

    formatter = logging.Formatter("[%(asctime)s %(levelname)s][%(name)s] %(message)s")
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    stream_handler.setLevel(level)

    logger = logging.getLogger(name)
    logger.addHandler(stream_handler)
    logger.setLevel(level)
    logger.propagate = False
