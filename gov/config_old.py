
# -*- coding: utf-8 -*-

import os
import argparse
from .errors import LostConfigFieldError


_CONFIG = {
    "__parsed_env": False,
    "__parsed_args": False,
    "__checked": False
}


class _BaseConfig():
    _FIELDS = ()
    _REQUIRED = ()
    _ARGS = ()
    _PREFIX = None
    _CFG = {}

    def __init__(self):
        _read_config()
        self._CFG = _CONFIG[self._PREFIX]


class DBConfig(_BaseConfig):
    """Config for working with database.
    """
    _FIELDS = ("HOST", "USER", "PASSWORD", "NAME", "ECHO", "PORT")
    _REQUIRED = ("HOST", "USER", "PASSWORD", "NAME", "PORT")
    _PREFIX = "DB"

    def __init__(self):
        super().__init__()
        if "echo" in self._CFG and self._CFG["echo"] is not None:
            self._CFG["echo"] = str.lower(self._CFG["echo"])

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

    @property
    def echo(self):
        return self._CFG.get("echo")

    @property
    def port(self):
        return self._CFG["port"]

class AppConfig(_BaseConfig):
    """The main application config.
    """
    _FIELDS = ("MODE", "FTP_SERVER", "TMP_FOLDER", "LIMIT_ARCHIVES", "LAW_NUMBER", "SERVER_FOLDER_NAME")
    _REQUIRED = ("FTP_SERVER", "TMP_FOLDER", "SERVER_FOLDER_NAME")
    _ARGS = ("SERVER_FOLDER_NAME", "LAW_NUMBER", "LIMIT_ARCHIVES")
    _PREFIX = "APP"
    _default_mode = "prod"
    _avail_modes = ("dev", _default_mode)
    _default_law = "44"
    _avail_laws = ("223", _default_law)

    def __init__(self):
        super().__init__()
        if "mode" not in self._CFG or self._CFG["mode"] not in self._avail_modes:
            self._CFG["mode"] = self._default_mode

        if "law_number" not in self._CFG or self._CFG["law_number"] not in self._avail_laws:
            self._CFG["law_number"] = self._default_law

        self.log = self._LogConfig()

        if self.mode == "dev" and not self.log._has_configured_level_value:
            self.log._CFG["level"] = "DEBUG"

        if "limit_archives" in self._CFG:
            self._CFG["limit_archives"] = int(self._CFG["limit_archives"])

    @property
    def mode(self):
        return str.lower(self._CFG["mode"])

    @property
    def ftp_server(self):
        return self._CFG["ftp_server"]

    @property
    def tmp_folder(self):
        return self._CFG["tmp_folder"]

    @property
    def limit_archives(self):
        return self._CFG.get("limit_archives")

    @property
    def law_number(self):
        return self._CFG["law_number"]

    @property
    def server_folder_name(self):
        return self._CFG["server_folder_name"]

    class _LogConfig(_BaseConfig):
        """Config for logger.
        """
        _FIELDS = ("LEVEL",)
        _PREFIX = "APP_LOG"
        _default_level = "INFO"
        _has_configured_level_value = True

        def __init__(self):
            super().__init__()
            if "level" not in self._CFG:
                self._CFG["level"] = self._default_level
                self._has_configured_level_value = False

        @property
        def level(self):
            return self._CFG["level"]


def _read_config():
    _read_env()
    _check_config()


def _is_env_read():
    return _CONFIG["__parsed_env"] is True


def _is_config_checked():
    return _CONFIG["__checked"] is True


def _read_env():
    if _is_env_read():
        return

    # идём по полям классов, читаём данные из ENV
    for cls in (DBConfig, AppConfig, AppConfig._LogConfig):
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
    if _is_config_checked():
        return

    for cls in (DBConfig, AppConfig, AppConfig._LogConfig):
        for field in cls._REQUIRED:
            lower_field = str.lower(field)
            env_field = cls._PREFIX + "_" + field
            if lower_field not in _CONFIG[cls._PREFIX] or _CONFIG[cls._PREFIX][lower_field] is None:
                raise LostConfigFieldError(env_field)

    _CONFIG["__checked"] = True

def conf(key):
    """Get config data"""
    pass
