
# -*- coding: utf-8 -*-

import os
from .log import get_logger
from .purchases import Client
from .db import DBClient
from .law.readers import FortyFourthLaw
from .config import AppConfig


log = get_logger(__name__)
db = DBClient()
ffl = FortyFourthLaw()
cfg = AppConfig()


def convert_finfo_to_dict(finfo: tuple) -> dict:
    """[summary]

    Args:
        finfo (tuple): [description]

    Returns:
        dict: [description]
    """
    finfo_dict = {
        "full_file": finfo[0],
        "fname": finfo[1],
        "fsize": int(finfo[2])
    }

    return finfo_dict


def has_archive(finfo: dict) -> bool:
    """Проверяет, нет ли у нас уже информации об этом файле

    Args:
        finfo (dict): Кортеж с данными о файле.

    Returns:
        bool: Результат проверки.
    """

    has_data_in_db = db.has_parsed_archive(finfo["full_file"], finfo["fname"], finfo["fsize"])
    return has_data_in_db


def handle_file(finfo: dict):
    """Работа со скачанным файлом. После обработки файл удаляется

    Args:
        finfo (dict): Кортеж с данными о файле.
    """

    log.info("File: {}; Size: {}".format(finfo["fname"], finfo["fsize"]))
    zip_file = cfg.tmp_folder + "/" + finfo["fname"]
    ffl.handle_archive(zip_file)

    # после работы подчищаем за собой
    if os.path.isfile(zip_file):
        log.info("Remove file {}".format(zip_file))
        os.remove(zip_file)


def run():
    """Главная функция. Запускаемся, читаем данные"""

    log.info("Init work")

    # подключаемся к FTP-серверу
    server = Client(cfg.ftp_server, download_dir=cfg.tmp_folder)

    count = 0  # FIXME: только для тестов
    # читаем файлы с архивами на сервере. При необходимости, загружаем себе
    for finfo in server.read():
        finfo_dict = convert_finfo_to_dict(finfo)
        if has_archive(finfo_dict):
            continue
        count += 1  # FIXME: только для тестов
        server.download(finfo_dict["full_file"], finfo_dict["fname"])
        handle_file(finfo)

        # FIXME: только для тестов
        if count >= 15:
            break
