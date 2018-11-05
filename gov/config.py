
# -*- coding: utf-8 -*-

import os
from .errors import LostConfigFieldError


_CONFIG = {}


class _BaseConfig():
    _FIELDS = ()
    _REQUIRED = _FIELDS
    _PREFIX = None
    _CFG = {}

    def __init__(self):
        _read_env()
        self._CFG = _CONFIG[self._PREFIX]


class DBConfig(_BaseConfig):
    """Класс для работы с конфигурацией базы данных.
    """
    _FIELDS = ("HOST", "USER", "PASSWORD", "NAME")
    _PREFIX = "DB"

    @property
    def host(self):
        return self._CFG["host"]

    @property
    def user(self):
        return self._CFG["user"]

    @property
    def password(self):
        return self._CFG["password"]

    @property
    def name(self):
        return self._CFG["name"]


class AppConfig(_BaseConfig):
    _FIELDS = ("MODE",)
    _REQUIRED = ()
    _PREFIX = "APP"
    _CFG = {"mode": "prod"}
    __avail_mode = ("dev", "prod")

    def __init__(self):
        super().__init__()
        if "mode" not in self._CFG or self._CFG["mode"] not in self.__avail_mode:
            self._CFG["mode"] = "prod"

    @property
    def mode(self):
        return str.lower(self._CFG["mode"])


def _read_env():
    if len(_CONFIG) > 0:
        return

    # идём по полям классов, читаём данные из ENV
    for cls in (DBConfig, AppConfig):
        for field in cls._FIELDS:
            env_field = cls._PREFIX + "_" + field
            if env_field not in os.environ and field in cls._REQUIRED:
                raise LostConfigFieldError(env_field)
            cfg_key = cls._PREFIX
            if cfg_key not in _CONFIG:
                _CONFIG[cfg_key] = {}
            _CONFIG[cfg_key][field.lower()] = os.environ.get(env_field)
