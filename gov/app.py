
# -*- coding: utf-8 -*-

import argparse
import os
from .log import get_logger
from .purchases import Client
from .law.readers import FortyFourthLaw


_SERVER = None
_TMP_FOLDER = None
log = get_logger(__name__)
ffl = FortyFourthLaw()


def read_args():
    """Считывает параментры из командной строки"""

    global _SERVER, _TMP_FOLDER

    parser = argparse.ArgumentParser()
    requiredNamed = parser.add_argument_group('required named arguments')
    requiredNamed.add_argument("-s", "--server", type=str, help="Server address", required=True)
    requiredNamed.add_argument("-t", "--tmp_folder", type=str,
                               help="Temporary folder for archives",
                               required=True)
    args = parser.parse_args()
    _SERVER = args.server
    _TMP_FOLDER = args.tmp_folder


def has_archive(finfo):
    """Проверяет, нет ли у нас уже информации об этом файле"""

    return False


def handle_file(finfo: tuple):
    """Работа со скачанным файлом.
    После обработки файл удаляется

    Args:
        finfo (tuple): кортеж с данными о файле
    """

    (fname, file_size) = (finfo[1], finfo[2])
    log.info("File: {}; Size: {}".format(fname, file_size))
    zip_file = _TMP_FOLDER + "/" + fname
    ffl.handle_archive(zip_file)

    # после работы подчищаем за собой
    if os.path.isfile(zip_file):
        log.info("Remove file {}".format(zip_file))
        os.remove(zip_file)


def run():
    """Главная функция. Запускаемся, читаем данные"""

    read_args()
    log.info("Init work")

    # подключаемся к FTP-серверу
    server = Client(_SERVER, download_dir=_TMP_FOLDER)

    count = 0
    # читаем файлы с архивами на сервере. При необходимости, загружаем себе
    for finfo in server.read():
        if has_archive(finfo):
            continue
        count += 1
        (full_file, fname) = (finfo[0], finfo[1])
        server.download(full_file, fname)
        handle_file(finfo)

        if count >= 15:
            break
