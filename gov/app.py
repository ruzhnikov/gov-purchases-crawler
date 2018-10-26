
# -*- coding: utf-8 -*-

import argparse
import os
from zipfile import ZipFile
from lxml import etree
from .log import get_logger
from .purchases import Client


_SERVER = None
_TMP_FOLDER = None
log = get_logger(__name__)


def read_args():
    global _SERVER, _TMP_FOLDER

    parser = argparse.ArgumentParser()
    requiredNamed = parser.add_argument_group('required named arguments')
    requiredNamed.add_argument("-s", "--server", type=str,
                            help="Server address", required=True)
    requiredNamed.add_argument(
        "-t", "--tmp_folder", type=str, help="Temporary folder for archives",
        required=True)
    args = parser.parse_args()
    _SERVER = args.server
    _TMP_FOLDER = args.tmp_folder        


def has_archive(finfo):
    """Проверяет, нет ли у нас уже информации об этом файле"""

    return False


def read_archive(archive, callback_func):
    """
        Читает ZIP-архив, извлекает из него XML-файлы.
        Для каждого прочитанного XML файла запускает callback функцию.
    """

    with ZipFile(archive, "r") as zip:
        for entry in zip.namelist():
            if not entry.endswith(".xml"):
                continue
            with zip.open(entry, "r") as f:
                xml = f.read()

            callback_func(xml)


def upload_xml(xml):
    """Парсит XML, загружает данные в БД"""

    root = etree.fromstring(xml)
    pass
    # etree.En


def handle_file(finfo: tuple):
    """Работает со скачанным файлом"""

    (fname, file_size) = (finfo[0], finfo[2])
    log.info("File: {}; Size: {}".format(fname, file_size))
    local_file = _TMP_FOLDER + "/" + fname
    read_archive(local_file, callback_func=upload_xml)

    # после работы подчищаем за собой
    if os.path.isfile(local_file):
        os.remove(local_file)


def run():
    """Главная функция. Запускаемся, читаем данные"""

    read_args()
    log.info("Init work")

    # подключаемся к FTP-серверу
    server = Client(_SERVER, download_dir=_TMP_FOLDER)

    # читаем файлы с архивами на сервере. При необходимости, загружаем себе
    for finfo in server.read():
        if has_archive(finfo):
            continue
        (full_file, fname) = (finfo[0], finfo[1])
        server.download(full_file, fname)
        handle_file(finfo)
        break

