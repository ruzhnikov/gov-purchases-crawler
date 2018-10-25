

import logging


_DEFAULT_LOGGER_NAME = "Crawler"
_DEFAULT_LOG_LEVEL = "INFO"
_LOG_FORMAT = "%(asctime)s | %(levelname)s | %(process)d | " \
    "%(name)s | %(filename)s:%(lineno)s | %(message)s"


def get_logger(logger_name=_DEFAULT_LOGGER_NAME, use_async=False):
    """Возвращает объект логгера"""

    l_name = "asyncio" if use_async else logger_name
    logger = logging.getLogger(l_name)
    logger.setLevel(_DEFAULT_LOG_LEVEL)
    log_handler = logging.StreamHandler()

    formatter = logging.Formatter(_LOG_FORMAT)
    log_handler.setFormatter(formatter)
    logger.addHandler(log_handler)

    return logger
