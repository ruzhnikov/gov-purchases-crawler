
# -*- coding: utf-8 -*-

import logging
from .config import AppConfig


_DEFAULT_LOGGER_NAME = "Crawler"
_LOG_FORMAT = "%(asctime)s | %(levelname)s | %(process)d | " \
    "%(name)s | %(filename)s:%(lineno)s | %(message)s"
cfg = AppConfig()


def get_logger(name=_DEFAULT_LOGGER_NAME, use_async=False):
    """Возвращает объект логгера"""

    logger_name = "asyncio" if use_async else name
    logging.basicConfig(format=_LOG_FORMAT, level=cfg.log.level)

    return logging.getLogger(logger_name)
