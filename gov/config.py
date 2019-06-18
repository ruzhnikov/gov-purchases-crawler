
# -*- coding: utf-8 -*-

"""Config module"""


import os
import argparse
import yaml
from .errors import LostConfigError
from .filters import parse_filter, get_help as filters_help


_ENV_FILE_CONFIG_NAME = "APP_CONFIG_FILE"
_ENV_SERVER_MODE = "APP_SERVER_MODE"
_ENV_FILTER = "APP_FILTERS"
_ENV_LOG_LEVEL = "APP_LOG_LEVEL"
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
_DEFAULT_DB_ECHO = False
_ARG_FILTER = "filters"


_cached_config = {}


def _load_conf():
    """Load data from config file. Append extra parameters"""

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
    """Add aditional keys to config"""

    if args[_ARG_SERVER_FOLDER_NAME] not in _AVAILABLE_FOLDERS:
        raise ValueError(f"{_ARG_SERVER_FOLDER_NAME} has to be in {[folder for folder in _AVAILABLE_FOLDERS]}")
    _cached_config["app"][_ARG_SERVER_FOLDER_NAME] = args[_ARG_SERVER_FOLDER_NAME]

    # set work mode
    _cached_config["app"][_ARG_SERVER_MODE] = _DEFAULT_APP_MODE

    if _ENV_SERVER_MODE in os.environ and os.environ[_ENV_SERVER_MODE] in _AVAILABLE_MODES:
        _cached_config["app"][_ARG_SERVER_MODE] = os.environ[_ENV_SERVER_MODE]
    elif _ARG_SERVER_MODE in args and args[_ARG_SERVER_MODE] in _AVAILABLE_MODES:
        _cached_config["app"][_ARG_SERVER_MODE] = args[_ARG_SERVER_MODE]

    # set limit archives
    if _ARG_LIMIT_ARCHIVES_NAME in args and type(
            args[_ARG_LIMIT_ARCHIVES_NAME]) is int and args[_ARG_LIMIT_ARCHIVES_NAME] > 0:
        _cached_config["app"][_ARG_LIMIT_ARCHIVES_NAME] = args[_ARG_LIMIT_ARCHIVES_NAME]
    else:
        _cached_config["app"][_ARG_LIMIT_ARCHIVES_NAME] = 0

    # set law number
    if _ARG_LAW_NUMBER in args:
        _cached_config["app"][_ARG_LAW_NUMBER] = args[_ARG_LAW_NUMBER]
    else:
        _cached_config["app"][_ARG_LAW_NUMBER] = _DEFAULT_LAW_NUMBER

    # set log parameters
    if _cached_config["app"]["log"]["level"] is None:
        _cached_config["app"]["log"]["level"] = _DEFAULT_LOG_LEVEL

    if _ENV_LOG_LEVEL in os.environ:
        _cached_config["app"]["log"]["level"] = os.environ[_ENV_LOG_LEVEL]

    # set DB echo mode
    if _cached_config["db"]["echo"] is None or _cached_config["db"]["echo"] is not bool:
        _cached_config["db"]["echo"] = _DEFAULT_DB_ECHO

    # add filter
    if _ENV_FILTER in os.environ or _ARG_FILTER in args:
        filter_str = os.environ.get(_ENV_FILTER)
        if filter_str is None or filter_str == "":
            filter_str = args[_ARG_FILTER]

    if filter_str is None:
        filter_str = "[]"

    _cached_config["app"]["filters"] = parse_filter(filter_str)


def _read_args() -> dict:
    """Read arguments from command line"""

    parser = argparse.ArgumentParser()

    parser.add_argument("-c", f"--{_ARG_FILE_CONFIG_NAME}", type=str, help="Config file")
    parser.add_argument("-l", f"--{_ARG_LIMIT_ARCHIVES_NAME}", type=int, help="Limit of archives")
    parser.add_argument("-m", f"--{_ARG_SERVER_MODE}", type=str, help="Work mode; 'dev' or 'prod'")
    parser.add_argument("-n", f"--{_ARG_LAW_NUMBER}", type=str, help="Law number")
    parser.add_argument("-F", f"--{_ARG_FILTER}", type=str, help=filters_help())
    requiredNamed = parser.add_argument_group('required named arguments')
    requiredNamed.add_argument("-f", f"--{_ARG_SERVER_FOLDER_NAME}", type=str,
                               help=f"Name of folder on server", required=True)

    args = parser.parse_args()

    return {
        _ARG_FILE_CONFIG_NAME: args.config_file,
        _ARG_LIMIT_ARCHIVES_NAME: args.limit_archives,
        _ARG_SERVER_FOLDER_NAME: args.server_folder_name,
        _ARG_SERVER_MODE: args.mode,
        _ARG_LAW_NUMBER: args.law_number,
        _ARG_FILTER: args.filters
    }


def _get_conf_by_key(key):
    """Get config data by separated key"""

    splitted_keys = str(key).split(".")
    if len(splitted_keys) == 1:
        return _get_conf(key)

    first_item = _get_conf(splitted_keys[0])
    if first_item is None or not isinstance(first_item, dict):
        return None

    local_cfg = first_item
    splitted_keys_len = len(splitted_keys)
    returned_value = None

    for i in range(1, splitted_keys_len):
        is_last_element = (i + 1) == splitted_keys_len
        local_key = splitted_keys[i]
        found_value = local_cfg.get(local_key)

        if found_value is None:
            returned_value = None
            break
        elif isinstance(found_value, dict):
            returned_value = local_cfg = found_value
        elif is_last_element:
            returned_value = found_value

    return returned_value


def _get_conf(key: str):
    if key in _cached_config:
        return _cached_config[key]

    return None


def conf(key=None):
    """Config container

    key (str, optional): Defaults to None. Config key.

    `key` can be either like just "aa" or "aa.bb.cc"

    If key has view as "aa.bb.cc", the resulted value will be searched in
        {"aa": {"bb": { "cc": "value" }}}
    If value for key was not found, `None` will be returned.
    """

    if not _cached_config:
        _load_conf()

    if key is None:
        return _cached_config

    return _get_conf_by_key(key)


def is_production() -> bool:
    """Is it production mode or no"""

    return conf("app.mode") == "prod"
