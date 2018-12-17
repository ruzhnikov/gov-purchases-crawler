
# -*- coding: utf-8 -*-

import pytest
import os
from gov import config as gov_config
from gov import errors


_PREDEFINED_CONFIG_FIELDS = {
    "app": {
        "mode": "dev",
        "ftp_server": "some.ftp.host",
        "tmp_folder": "local_tmp",
        "limit_archives": "10",
    },
    "app_log": {
        "level": "DEBUG"
    },
    "db": {
        "host": "some.db.host",
        "user": "db_user",
        "password": "db_password",
        "name": "db_name",
        "echo": "no"
    }
}


def clean_global_config():
    gov_config._CONFIG = {
        "__parsed_env": False,
        "__checked": False
    }
    for cls in (gov_config.AppConfig, gov_config.AppConfig.LogConfig, gov_config.DBConfig):
        cls_prefix = cls._PREFIX
        for field in cls._FIELDS:
            cfg_field = cls_prefix + "_" + field
            if cfg_field in os.environ:
                del os.environ[cfg_field]


def test_normal_run_with_all_fields():
    clean_global_config()
    assert gov_config._is_env_read() is False
    assert gov_config._is_config_checked() is False

    for key in _PREDEFINED_CONFIG_FIELDS.keys():
        for local_key in _PREDEFINED_CONFIG_FIELDS[key].keys():
            env_key = str.upper(key) + "_" + str.upper(local_key)
            os.environ[env_key] = _PREDEFINED_CONFIG_FIELDS[key][local_key]

    app_cfg = gov_config.AppConfig()
    db_cfg = gov_config.DBConfig()
    log_cfg = gov_config.AppConfig.LogConfig()

    assert app_cfg is not None
    assert db_cfg is not None
    assert log_cfg is not None

    predef_app_cfg = _PREDEFINED_CONFIG_FIELDS["app"]
    assert app_cfg.mode == predef_app_cfg["mode"]
    assert app_cfg.tmp_folder == predef_app_cfg["tmp_folder"]
    assert app_cfg.ftp_server == predef_app_cfg["ftp_server"]
    assert type(app_cfg.limit_archives) is int
    assert app_cfg.limit_archives == int(predef_app_cfg["limit_archives"])

    predef_log_cfg = _PREDEFINED_CONFIG_FIELDS["app_log"]
    assert log_cfg.level == predef_log_cfg["level"]

    predef_db_cfg = _PREDEFINED_CONFIG_FIELDS["db"]
    assert db_cfg.host == predef_db_cfg["host"]
    assert db_cfg.user == predef_db_cfg["user"]
    assert db_cfg.password == predef_db_cfg["password"]
    assert db_cfg.name == predef_db_cfg["name"]
    assert db_cfg.echo == predef_db_cfg["echo"]


def test_normal_run_with_required_fields():
    clean_global_config()
    assert gov_config._is_env_read() is False
    assert gov_config._is_config_checked() is False

    local_predef_cfg = {
        gov_config.AppConfig: _PREDEFINED_CONFIG_FIELDS["app"],
        gov_config.AppConfig.LogConfig: _PREDEFINED_CONFIG_FIELDS["app_log"],
        gov_config.DBConfig: _PREDEFINED_CONFIG_FIELDS["db"]
    }

    for cls in (gov_config.AppConfig, gov_config.AppConfig.LogConfig, gov_config.DBConfig):
        local_cfg = local_predef_cfg[cls]
        for required_field in cls._REQUIRED:
            local_value = local_cfg[str.lower(required_field)]
            os.environ[cls._PREFIX + "_" + required_field] = local_value

    app_cfg = gov_config.AppConfig()
    db_cfg = gov_config.DBConfig()
    log_cfg = gov_config.AppConfig.LogConfig()

    assert app_cfg is not None
    assert db_cfg is not None
    assert log_cfg is not None

    predef_app_cfg = _PREDEFINED_CONFIG_FIELDS["app"]
    assert app_cfg.ftp_server == predef_app_cfg["ftp_server"]
    assert app_cfg.tmp_folder == predef_app_cfg["tmp_folder"]
    assert app_cfg.limit_archives is None
    assert app_cfg.mode == app_cfg._default_mode

    assert log_cfg.level == log_cfg._default_level


def test_read_env():
    clean_global_config()

    gov_config._CONFIG["parsed_env"] = True
    assert not gov_config._read_env()


# def test_check_config():
#     clean_global_config()
#     try:
#         gov_config._check_config()
#     except errors.LostConfigFieldError as e:
#         assert e.message is not None
