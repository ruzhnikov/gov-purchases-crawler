
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


_NEED_TO_UPDATE_ARCHIVE = False


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
    """Проверяет, нет ли у нас уже информации об этом архиве.

    Args:
        finfo (dict): Словарь с данными об архиве.

    Returns:
        bool: Результат проверки.
    """

    _NEED_TO_UPDATE_ARCHIVE = False
    arch_status = db.get_archive_status(finfo["full_name"], finfo["fname"], finfo["fsize"])
    if arch_status == db.FILE_STATUS["FILE_EXISTS"]:
        return True
    elif arch_status == db.FILE_STATUS["FILE_DOES_NOT_EXIST"]:
        return False
    elif arch_status in (db.FILE_STATUS["FILE_EXISTS_BUT_NOT_PARSED"],
                         db.FILE_STATUS["FILE_EXISTS_BUT_SIZE_DIFFERENT"]):
        _NEED_TO_UPDATE_ARCHIVE = True
        return True


def need_to_update_archive():
    return _NEED_TO_UPDATE_ARCHIVE


def handle_archive(finfo: dict):
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


def update_archive(finfo: dict):
    pass


def run():
    """Главная функция. Запускаемся, читаем данные"""

    log.info("Init work")

    # подключаемся к FTP-серверу
    server = Client(cfg.ftp_server, download_dir=cfg.tmp_folder)

    count = 0  # FIXME: только для тестов
    # читаем файлы с архивами на сервере. При необходимости, загружаем себе
    for f in server.read():
        fdict = convert_finfo_to_dict(f)
        if has_archive(fdict):
            if need_to_update_archive():
                server.download(fdict["full_file"], fdict["fname"])
                update_archive(fdict)
            continue
        count += 1  # FIXME: только для тестов

        # Скачиваем файл и сохраняем информацию о нём в БД. Далее, читаем его.
        server.download(fdict["full_file"], fdict["fname"])
        fdict["archive_id"] = db.add_archive(fdict["full_file"], fdict["fname"], fdict["fsize"])
        handle_archive(fdict)

        # FIXME: только для тестов
        if count >= 15:
            break
