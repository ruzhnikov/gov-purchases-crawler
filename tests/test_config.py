
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
        "level": "WARNING"
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
    for cls in (gov_config.AppConfig, gov_config.AppConfig._LogConfig, gov_config.DBConfig):
        cls_prefix = cls._PREFIX
        for field in cls._FIELDS:
            cfg_field = cls_prefix + "_" + field
            if cfg_field in os.environ:
                del os.environ[cfg_field]


def fill_env_by_normal_values():
    for key in _PREDEFINED_CONFIG_FIELDS.keys():
        for local_key in _PREDEFINED_CONFIG_FIELDS[key].keys():
            env_key = str.upper(key) + "_" + str.upper(local_key)
            os.environ[env_key] = _PREDEFINED_CONFIG_FIELDS[key][local_key]


def fill_env_by_required_values():
    local_predef_cfg = {
        gov_config.AppConfig: _PREDEFINED_CONFIG_FIELDS["app"],
        gov_config.AppConfig._LogConfig: _PREDEFINED_CONFIG_FIELDS["app_log"],
        gov_config.DBConfig: _PREDEFINED_CONFIG_FIELDS["db"]
    }

    # set up enviroment variables by gov.config classes required fields
    for cls in local_predef_cfg.keys():
        local_cfg = local_predef_cfg[cls]
        for required_field in cls._REQUIRED:
            local_value = local_cfg[str.lower(required_field)]
            os.environ[cls._PREFIX + "_" + required_field] = local_value


def test_local_predefined_settings():
    clean_global_config()

    local_predef_cfg = {
        gov_config.AppConfig: _PREDEFINED_CONFIG_FIELDS["app"],
        gov_config.AppConfig._LogConfig: _PREDEFINED_CONFIG_FIELDS["app_log"],
        gov_config.DBConfig: _PREDEFINED_CONFIG_FIELDS["db"]
    }

    for cls in local_predef_cfg.keys():
        local_cfg = local_predef_cfg[cls]
        for field in cls._FIELDS:
            lower_field = str.lower(field)
            assert lower_field in local_cfg

class TestNormalRun():
    def setup(self):
        clean_global_config()

    def test_normal_run_with_all_fields(self):
        assert gov_config._is_env_read() is False
        assert gov_config._is_config_checked() is False

        fill_env_by_normal_values()

        app_cfg = gov_config.AppConfig()
        db_cfg = gov_config.DBConfig()
        log_cfg = gov_config.AppConfig._LogConfig()

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

    def test_normal_run_with_required_fields(self):
        assert gov_config._is_env_read() is False
        assert gov_config._is_config_checked() is False

        # set local predefined config
        fill_env_by_required_values()

        app_cfg = gov_config.AppConfig()
        db_cfg = gov_config.DBConfig()
        log_cfg = gov_config.AppConfig._LogConfig()

        assert app_cfg is not None
        assert db_cfg is not None
        assert log_cfg is not None

        predef_app_cfg = _PREDEFINED_CONFIG_FIELDS["app"]
        assert app_cfg.ftp_server == predef_app_cfg["ftp_server"]
        assert app_cfg.tmp_folder == predef_app_cfg["tmp_folder"]
        assert app_cfg.limit_archives is None
        assert app_cfg.mode == app_cfg._default_mode


class TestAppConfig():
    def setup(self):
        clean_global_config()

    def test_default_mode_set(self):
        fill_env_by_required_values()
        app_cfg = gov_config.AppConfig()

        assert app_cfg.limit_archives is None
        assert app_cfg.mode is not None
        assert app_cfg.mode == app_cfg._default_mode

    def test_default_log_level(self):
        fill_env_by_required_values()
        os.environ["APP_MODE"] = "dev"
        app_cfg = gov_config.AppConfig()
        log_cfg = app_cfg.log

        assert log_cfg.level == "DEBUG"

        clean_global_config()
        fill_env_by_required_values()
        os.environ["APP_MODE"] = "prod"
        app_cfg = gov_config.AppConfig()
        log_cfg = app_cfg.log

        assert log_cfg.level == log_cfg._default_level

    def test_log_config(self):
        fill_env_by_normal_values()

        log_cls = gov_config.AppConfig._LogConfig
        log_prefix = log_cls._PREFIX
        os.environ[log_prefix + "_LEVEL"] = "WARNING"

        app_cfg = gov_config.AppConfig()
        log_cfg = gov_config.AppConfig._LogConfig()

        assert app_cfg.log.level == log_cfg.level

    def test_set_log_level_and_dev_mode(self):
        fill_env_by_required_values()
        os.environ["APP_MODE"] = "dev"
        os.environ["APP_LOG_LEVEL"] = "WARNING"

        app_cfg = gov_config.AppConfig()
        log_cfg = app_cfg.log

        assert log_cfg.level == "WARNING"

