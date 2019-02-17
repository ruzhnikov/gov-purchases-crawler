
# -*- coding: utf-8 -*-

import logging
from .config import conf


_DEFAULT_LOGGER_NAME = "Crawler"
_LOG_FORMAT = "%(asctime)s | %(levelname)s | %(process)d | " \
    "%(filename)s:%(lineno)s | %(message)s"
cfg = conf("app")


def get_logger(name=_DEFAULT_LOGGER_NAME, use_async=False):
    """Logger object"""

    logger_name = "asyncio" if use_async else name
    logging.basicConfig(format=_LOG_FORMAT, level=cfg["log"]["level"])

    return logging.getLogger(logger_name)
