
# -*- coding: utf-8 -*-

from ftplib import FTP
from .log import get_logger
from .errors import EmptyDownloadDirError


_FTP_LOGIN = "free"
_FTP_PASSWORD = "free"
_FTP_ROOT_DIR = "/fcs_regions"

# папка в директории региона. Из этой папки будем выкачивать данные
_DEFAULT_LOOK_FOLDER = "notifications"


class Client():
    """Класс для работы с FTP сервером"""

    def __init__(self, server_address, download_dir=None, looking_folder=_DEFAULT_LOOK_FOLDER):
        self._server = server_address
        self.log = get_logger(__name__)
        self._is_connected = False
        self._root_folders = []
        self._skipped_region = None
        self._download_dir = download_dir
        self._looking_folder = looking_folder
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
        for region in self._root_folders:
            self.log.info(f"Read folder {region}")
            if self._skipped_region is not None:
                skipped_region = self._skipped_region
                self._skipped_region = None
                if skipped_region == region:
                    continue

            full_folder = _FTP_ROOT_DIR + "/" + region + "/" + self._looking_folder
            yield from self._read_folder_with_archives(full_folder, region)

    def set_region_skipped(self, region: str):
        self._skipped_region = region

    def _read_root_folders(self):
        """Получить папки с регионами из корневой директории"""

        self.ftp.cwd(_FTP_ROOT_DIR)
        items = []
        self.ftp.retrlines("LIST", items.append)
        items = map(str.split, items)
        self._root_folders = [item.pop()
                              for item in items if item[0][0] == 'd']

    def _read_folder_with_archives(self, folder: str, region: str):
        """Прочитать файлы из указанной папки.
        Вложенные папки также будут прочитаны. Возвращает итератор

        Args:
            folder (str): имя папки
        """

        # для начала читаем папку
        self.ftp.cwd(folder)
        self.log.info(f"Read files of directory {folder}")
        items = []
        self.ftp.retrlines("LIST", items.append)
        items = map(str.split, items)

        # идём по списку файлов
        for item in items:
            if self._skipped_region is not None and self._skipped_region == region:
                self._leave_current_directory()
                break

            item_type = item[0][0]
            if item_type == "d":

                # это директория. Вызовём для неё рекурсивно сами себя
                local_folder = item.pop()
                self.log.info(f"Go inside {local_folder}")
                yield from self._read_folder_with_archives(folder + "/" + local_folder, region)

                # После работы нужно вернуться в предыдущую папку
                self.log.info(f"Leave {local_folder}")
                self._leave_current_directory()
            else:

                # это файл, читаем информацию о нём и возвращаем её
                file = item.pop()
                full_file = folder + "/" + file
                file_size = item[4]
                yield {
                    "full_name": full_file,
                    "fname": file,
                    "fsize": int(file_size),
                    "region": region
                }

    def _leave_current_directory(self):
        self.ftp.cwd("../")

    def download(self, fpath, fname, download_dir=None):
        """Скачать файл

        Args:
            fpath (str): Файл на сервере с указанием абсолютного пути до него
            fname (str): Имя файла
            download_dir (str, optional): Defaults to None. Диретория для скачивания

        Raises:
            EmptyDownloadDirError: Отсутствует папка для скачивания файла.
        """

        if download_dir is None:
            if self._download_dir is None:
                raise EmptyDownloadDirError
            download_dir = self._download_dir

        path_to_download = download_dir + "/" + fname
        self.ftp.retrbinary(f"RETR {fpath}", open(path_to_download, "wb").write)
