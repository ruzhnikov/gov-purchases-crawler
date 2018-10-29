
# -*- coding: utf-8 -*-

from ftplib import FTP
from .log import get_logger


_FTP_LOGIN = "free"
_FTP_PASSWORD = "free"
_FTP_ROOT_DIR = "/fcs_regions"

# папка в директории региона. Из этой папки будем выкачивать данные
_LOOK_FOLDER = "notifications"


class Client():
    """Класс для работы с FTP сервером"""


    def __init__(self, server_address, download_dir=None):
        self._server = server_address
        self.log = get_logger(__name__)
        self._is_connected = False
        self._root_folders = []
        self._download_dir = download_dir
        self._connect()


    def _connect(self):
        """Подключение и авторизация на FTP сервере"""

        self.ftp = FTP(self._server)
        self.ftp.login(_FTP_LOGIN, _FTP_PASSWORD)
        self._is_connected = True


    def reconnect(self):
        """Попытка переподключиться к серверу"""

        self._is_connected = False
        self._connect()

        return self._is_connected


    def read(self):
        """Читает файлы в папках, возвращает итератор"""

        self._read_root_folders()
        for folder in self._root_folders:
            self.log.info("Read folder {}".format(folder))
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
            if item_type == "d":

                # это директория. Вызовём для неё рекурсивно сами себя
                local_folder = item.pop()
                self.log.info("Go inside {}".format(local_folder))
                yield from self._read_folder_with_archives(folder + "/" + local_folder)

                # После работы нужно вернуться в предыдущую папку
                self.log.info("Leave {}".format(local_folder))
                self.ftp.cwd("../")
            else:

                # это файл, читаем информацию о нём и возвращаем её
                file = item.pop()
                full_file = folder + "/" + file
                file_size = item[4]
                yield (full_file, file, file_size)


    def download(self, fpath, fname, download_dir=None):
        """Скачать файл"""

        if download_dir is None:
            if self._download_dir is None:
                raise Exception(
                    "There is no folder to download file from ftp")
            download_dir = self._download_dir

        path_to_download = download_dir + "/" + fname
        self.ftp.retrbinary("RETR {}".format(fpath), open(path_to_download, "wb").write)

