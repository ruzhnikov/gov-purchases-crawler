
# -*- coding: utf-8 -*-

import argparse
import os
from zipfile import ZipFile
from lxml import etree
from .log import get_logger
from . import purchases


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


def read_archive(archive, callback):
    """
        Читает ZIP-архив, извлекает из него XML-файлы.
        Для каждого прочитанного XML файла запускает callback функцию.
    """

    with ZipFile(archive, "r") as zip:
        for entry in zip.namelist():
            if not entry.endswith(".xml"): continue
            with zip.open(entry, "r") as f:
                xml = f.read()

            callback(xml)


def upload_xml(xml):
    """Парсит XML, загружает данные в БД"""

    root = etree.fromstring(xml)
    pass
    # etree.En



def run():
    """Главная функция. Запускаемся, читаем данные"""

    read_args()
    log.info("Init work")

    # подключаемся к FTP-серверу
    server = purchases.Client(_SERVER, _TMP_FOLDER)

    # читаем файлы с архивами на сервере. При необходимости, загружаем себе
    for finfo in server.read():
        if has_archive(finfo): continue
        full_file = finfo[0]
        fname = finfo[1]
        file_size = finfo[2]
        log.info("File: {}; Size: {}".format(fname, file_size))
        server.download(full_file, fname)
        read_archive(_TMP_FOLDER + "/" + fname, callback=upload_xml)
        break

