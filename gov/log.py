
# -*- coding: utf-8 -*-

import logging


_DEFAULT_LOGGER_NAME = "Crawler"
_DEFAULT_LOG_LEVEL = logging.INFO
_LOG_FORMAT = "%(asctime)s | %(levelname)s | %(process)d | " \
    "%(name)s | %(filename)s:%(lineno)s | %(message)s"


def get_logger(name=_DEFAULT_LOGGER_NAME, use_async=False):
    """Возвращает объект логгера"""

    logger_name = "asyncio" if use_async else name
    logging.basicConfig(format=_LOG_FORMAT, level=_DEFAULT_LOG_LEVEL)

    return logging.getLogger(logger_name)
