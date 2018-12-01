
# -*- coding: utf-8 -*-

import os
import argparse
from .errors import LostConfigFieldError


_CONFIG = {
    "__parsed_env": False,
    "__checked": False
}


class _BaseConfig():
    _FIELDS = ()
    _REQUIRED = _FIELDS
    _PREFIX = None
    _CFG = {}

    def __init__(self):
        _read_config()
        self._CFG = _CONFIG[self._PREFIX]


class DBConfig(_BaseConfig):
    """Класс для работы с конфигурацией базы данных.
    """
    _FIELDS = ("HOST", "USER", "PASSWORD", "NAME")
    _REQUIRED = _FIELDS
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
    _FIELDS = ("MODE", "FTP_SERVER", "TMP_FOLDER")
    _REQUIRED = ("FTP_SERVER", "TMP_FOLDER")
    _PREFIX = "APP"
    __avail_mode = ("dev", "prod")

    def __init__(self):
        super().__init__()
        if "mode" not in self._CFG or self._CFG["mode"] not in self.__avail_mode:
            self._CFG["mode"] = "prod"
        self.log = self.LogConfig()
        if self.mode == "dev":
            self.log._CFG["level"] = "DEBUG"

    @property
    def mode(self):
        return str.lower(self._CFG["mode"])

    @property
    def ftp_server(self):
        return self._CFG["ftp_server"]

    @property
    def tmp_folder(self):
        return self._CFG["tmp_folder"]

    class LogConfig(_BaseConfig):
        _FIELDS = ("LEVEL")
        _PREFIX = "APP_LOG"
        __default_level = "INFO"

        def __init__(self):
            super().__init__()
            if "level" not in self._CFG:
                self._CFG["level"] = self.__default_level

        @property
        def level(self):
            return self._CFG["level"]


def _read_config():
    _read_env()
    _check_config()


def _read_env():
    if _CONFIG["__parsed_env"]:
        return

    # идём по полям классов, читаём данные из ENV
    for cls in (DBConfig, AppConfig, AppConfig.LogConfig):
        for field in cls._FIELDS:
            env_field = cls._PREFIX + "_" + field
            cfg_key = cls._PREFIX
            if cfg_key not in _CONFIG:
                _CONFIG[cfg_key] = {}
            if env_field not in os.environ:
                continue
            _CONFIG[cfg_key][field.lower()] = os.environ.get(env_field)
    _CONFIG["__parsed_env"] = True


def _check_config():
    if _CONFIG["__checked"]:
        return

    for cls in (DBConfig, AppConfig, AppConfig.LogConfig):
        for field in cls._REQUIRED:
            lower_field = str.lower(field)
            env_field = cls._PREFIX + "_" + field
            if lower_field not in _CONFIG[cls._PREFIX] or _CONFIG[cls._PREFIX][lower_field] is None:
                raise LostConfigFieldError(env_field)

    _CONFIG["__checked"] = True
