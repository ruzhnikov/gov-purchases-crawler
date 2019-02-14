
# -*- coding: utf-8 -*-

"""Config module"""


import os
import argparse


_ENV_FILE_CONFIG_NAME = "APP_CONFIG_FILE"
_ENV_LIMIT_ARCHIVES_NAME = "APP_LIMIT_ARCHIVES"
_ENV_SERVER_FOLDER_NAME = "APP_SERVER_FOLDER_NAME"
_ARG_FILE_CONFIG_NAME = "config_file"
_ARG_LIMIT_ARCHIVES_NAME = "limit_archives"
_ARG_SERVER_FOLDER_NAME = "server_folder_name"

_cached_config = {}


def _load_conf():
    pass


def _read_args() -> dict:
    pass


def conf(key=None):
    """Config container

        key (str, optional): Defaults to None. Config key.
    """

    if len(_cached_config) == 0:
        _load_conf()

    if key is None:
        return _get_conf(key)

    splitted_keys = str(key).split(".")
    if len(splitted_keys) == 1:
        return _get_conf(key)

    # root_conf = {}
    # for local_key in splitted_keys:
    #     local_conf = _get_conf(local_key)
    #     if local_conf is None:
    #         return None
        


def _get_conf(key: str):
    if key in _cached_config:
        return _cached_config[key]

    return None
