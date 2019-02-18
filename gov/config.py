
# -*- coding: utf-8 -*-

"""Config module"""


import os
import argparse
import yaml
from .errors import LostConfigError


_ENV_FILE_CONFIG_NAME = "APP_CONFIG_FILE"
_ENV_SERVER_MODE = "APP_SERVER_MODE"
_ARG_FILE_CONFIG_NAME = "config_file"
_ARG_LIMIT_ARCHIVES_NAME = "limit_archives"
_ARG_SERVER_FOLDER_NAME = "server_folder_name"
_ARG_LAW_NUMBER = "law_number"
_ARG_SERVER_MODE = "mode"
_AVAILABLE_MODES = ("dev", "prod")
_DEFAULT_APP_MODE = "dev"
_DEFAULT_LAW_NUMBER = "44"
_AVAILABLE_FOLDERS = ("protocols", "notifications")
_DEFAULT_LOG_LEVEL = "INFO"


_cached_config = {}


def _load_conf():
    args = _read_args()

    if _ENV_FILE_CONFIG_NAME in os.environ:
        cfg_file = os.environ[_ENV_FILE_CONFIG_NAME]
    else:
        cfg_file = args[_ARG_FILE_CONFIG_NAME] if _ARG_FILE_CONFIG_NAME in args else None

    if cfg_file is None:
        raise LostConfigError("Do you forget give config file? Try to do it by "
                         f"{_ENV_FILE_CONFIG_NAME} environmet or --{_ARG_FILE_CONFIG_NAME} argument")

    if not os.path.exists(cfg_file):
        raise FileNotFoundError(cfg_file)

    global _cached_config
    with open(cfg_file, "rt") as f:
        _cached_config = yaml.load(f)

    _fill_extra_pros(args)

    return True


def _fill_extra_pros(args):
    """added aditional keys to config"""

    if args[_ARG_SERVER_FOLDER_NAME] not in _AVAILABLE_FOLDERS:
        raise ValueError(f"{_ARG_SERVER_FOLDER_NAME} has to be in {[folder for folder in _AVAILABLE_FOLDERS]}")
    _cached_config["app"][_ARG_SERVER_FOLDER_NAME] = args[_ARG_SERVER_FOLDER_NAME]

    if _ARG_SERVER_MODE in args and args[_ARG_SERVER_MODE] in _AVAILABLE_MODES:
        _cached_config["app"][_ARG_SERVER_MODE] = args[_ARG_SERVER_MODE]
    else:
        _cached_config["app"][_ARG_SERVER_MODE] = _DEFAULT_APP_MODE

    if _ARG_LIMIT_ARCHIVES_NAME in args and args[_ARG_LIMIT_ARCHIVES_NAME] > 0:
        _cached_config["app"][_ARG_LIMIT_ARCHIVES_NAME] = args[_ARG_LIMIT_ARCHIVES_NAME]
    else:
        _cached_config["app"][_ARG_LIMIT_ARCHIVES_NAME] = 0

    if _ARG_LAW_NUMBER in args:
        _cached_config["app"][_ARG_LAW_NUMBER] = args[_ARG_LAW_NUMBER]
    else:
        _cached_config["app"][_ARG_LAW_NUMBER] = _DEFAULT_LAW_NUMBER

    if _cached_config["app"]["log"]["level"] is None:
        _cached_config["app"]["log"]["level"] = _DEFAULT_LOG_LEVEL


def _read_args() -> dict:
    parser = argparse.ArgumentParser()

    parser.add_argument("-c", f"--{_ARG_FILE_CONFIG_NAME}", type=str, help="Config file")
    parser.add_argument("-l", f"--{_ARG_LIMIT_ARCHIVES_NAME}", type=int, help="Limit of archives")
    parser.add_argument("-m", f"--{_ARG_SERVER_MODE}", type=str, help="Work mode; 'dev' or 'prod'")
    parser.add_argument("-n", f"--{_ARG_LAW_NUMBER}", type=str, help="Law number")
    requiredNamed = parser.add_argument_group('required named arguments')
    requiredNamed.add_argument("-f", f"--{_ARG_SERVER_FOLDER_NAME}", type=str,
                               help=f"Name of folder on server", required=True)

    args = parser.parse_args()

    return {
        _ARG_FILE_CONFIG_NAME: args.config_file,
        _ARG_LIMIT_ARCHIVES_NAME: args.limit_archives,
        _ARG_SERVER_FOLDER_NAME: args.server_folder_name,
        _ARG_SERVER_MODE: args.mode,
        _ARG_LAW_NUMBER: args.law_number
    }


# TODO: finish this function
def _get_conf_by_key(key):
    """Get config data by separated key

        key can be "aa.bb.cc"
    """

    splitted_keys = str(key).split(".")
    if len(splitted_keys) == 1:
        return _get_conf(key)

    first_item = _get_conf(splitted_keys[0])
    if first_item is None:
        return None

    returned_data = None
    # local_conf = first_item
    # splitted_keys_len = len(splitted_keys)
    # for i in range(1, splitted_keys_len):
    #     if isinstance(local_conf, dict):
    #         print(local_conf)
    #         local_key = splitted_keys[i]
    #         print(local_key)
    #         if local_key in local_conf:
    #             local_conf = local_conf[local_key]
    #         else:
    #             return None
    #         if i == splitted_keys:
    #             return local_conf
    #     else:
    #         print(type(local_conf))
    #         print(local_conf)
    #         return local_conf if i == splitted_keys else None

    return returned_data


def _get_conf(key: str):
    if key in _cached_config:
        return _cached_config[key]

    return None


def conf(key=None):
    """Config container

        key (str, optional): Defaults to None. Config key.
    """

    if len(_cached_config) == 0:
        _load_conf()

    if key is None:
        return _cached_config

    # return _get_conf_by_key(key)
    return _get_conf(key)


def is_production() -> bool:
    """Is it production mode or not"""

    return _cached_config["app"]["mode"] == "prod"
