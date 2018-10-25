
# -*- coding: utf-8 -*-

from ftplib import FTP
from .log import get_logger


_FTP_LOGIN = "free"
_FTP_PASSWORD = "free"
_FTP_ROOT_DIR = "/fcs_regions"

# папка в директории региона. Из этой папки будем выкачивать данные
_LOOK_FOLDER = "notifications"


class Client():
    def __init__(self, server):
        self._server = server
        self.log = get_logger()
        self._is_connected = False
        self._root_folders = []
        self._connect()

    def _connect(self):
        self.ftp = FTP(self._server)
        self.ftp.login(_FTP_LOGIN, _FTP_PASSWORD)
        self._is_connected = True

    def read(self):
        """Читает файлы в папках, возвращает итератор"""

        self._read_root_folders()
        for folder in self._root_folders:
            full_folder = _FTP_ROOT_DIR + "/" + folder + "/" + _LOOK_FOLDER
            yield from self._read_folder_with_archives(full_folder)

    def _read_root_folders(self):
        """Получить папки с регионами из корневой директории"""

        self.ftp.cwd(_FTP_ROOT_DIR)
        items = []
        self.ftp.retrlines("LIST", items.append)
        items = map(str.split, items)
        self._root_folders = [item.pop()
                              for item in items if item[0][0] == 'd']

    def _read_folder_with_archives(self, folder):
        """
            Прочитать файлы из указанной папки.
            Вложенные папки также будут прочитаны. Возвращает итератор
        """

        # для начала читаем папку
        self.ftp.cwd(folder)
        self.log.info("Read files of directory {}".format(folder))
        items = []
        self.ftp.retrlines("LIST", items.append)
        items = map(str.split, items)

        # идём по списку файлов
        for item in items:
            item_type = item[0][0]
            if item_type == "d": # directory
                local_folder = item.pop()
                self.log.info("Go inside {}".format(local_folder))
                yield from self._read_folder_with_archives(folder + "/" + local_folder)
                self.ftp.cwd("../")
            else:
                file = item.pop()
                full_file = folder + "/" + file
                file_size = item[4]
                yield (full_file, file, file_size)


