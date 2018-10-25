
# -*- coding: utf-8 -*-

import argparse
from .log import get_logger
from . import purchases

_SERVER = None

# папка в директории региона. Из этой папки будем выкачивать данные
_NEEDED_FOLDER = "notifications"

def read_args():
    global _SERVER

    parser = argparse.ArgumentParser()
    requiredNamed = parser.add_argument_group('required named arguments')
    requiredNamed.add_argument("-s", "--server", type=str,
                            help="Server address", required=True)
    args = parser.parse_args()
    _SERVER = args.server

def get_server():
    return _SERVER

def has_archive(file):
    """Проверяет, нет ли у нас уже информации об этом файле"""

    return False

def run():
    log = get_logger()
    log.info("Init work")
    read_args()

    server_addr = get_server()
    server = purchases.Client(server_addr)

    for finfo in server.read():
        # full_file = finfo[0]
        fname = finfo[1]
        file_size = finfo[2]
        log.info("File: {}; Size: {}".format(fname, file_size))

if __name__ == "__main__":
    run()
