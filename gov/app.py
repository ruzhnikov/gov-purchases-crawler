
# -*- coding: utf-8 -*-

import os
from .log import get_logger
from .purchases import Client
from .db import DBClient
from .law.readers import FortyFourthLawNotifications
from .config import AppConfig


class _Application():

    def __init__(self):
        self.log = get_logger(__name__)
        self.db = DBClient()
        self.ffl = FortyFourthLawNotifications()
        self.cfg = AppConfig()
        self._archives = {}

    def _has_archive(self, finfo: dict) -> bool:
        """Проверяет, нет ли у нас уже информации об этом архиве.

        Args:
            finfo (dict): Словарь с данными об архиве.

        Returns:
            bool: Результат проверки.
        """

        self._archives[finfo["full_name"]] = {"need_to_update": False}
        archive = self._archives[finfo["full_name"]]

        # Смотрим, что у нас в БД по этому файлу. Может быть ситуация, что файл в БД имеется и он
        # был прочитан и распарсен, но метаданные между ним и файлом с FTP сервера отличаются.
        # В таком случае нам нужно обновить данные в БД.
        arch_status = self.db.get_archive_status(finfo["full_name"], finfo["fname"], finfo["fsize"])
        if arch_status == self.db.FILE_STATUS["FILE_EXISTS"]:
            return True
        elif arch_status == self.db.FILE_STATUS["FILE_DOES_NOT_EXIST"]:
            return False
        elif arch_status in (self.db.FILE_STATUS["FILE_EXISTS_BUT_NOT_PARSED"],
                             self.db.FILE_STATUS["FILE_EXISTS_BUT_SIZE_DIFFERENT"]):
            archive["need_to_update"] = True
            return True

        return False

    def _need_to_update_archive(self, finfo: dict) -> bool:
        """Проверяет, нужно ли нам обновить информацию об архиве.

        Args:
            finfo (dict): Словарь с данными об архиве.

        Returns:
            bool: Результат проверки.
        """
        if finfo["full_name"] not in self._archives:
            self.log.warn(f"There is no information about archive {finfo} inside me")
            return False

        archive = self._archives[finfo["full_name"]]
        return archive["need_to_update"]

    def _handle_archive(self, finfo: dict):
        """Работа со скачанным файлом. После обработки файл удаляется

        Args:
            finfo (dict): Кортеж с данными о файле.
        """

        self.log.info(f"File: {finfo['fname']}; Size: {finfo['fsize']}")
        zip_file = self.cfg.tmp_folder + "/" + finfo["fname"]
        self.ffl.handle_archive(zip_file, finfo["id"])

        # после работы подчищаем за собой
        if os.path.isfile(zip_file):
            self.log.debug(f"Remove file {zip_file}")
            os.remove(zip_file)

            self.log.debug("Clean archive info")
            if finfo["full_name"] in self._archives:
                del self._archives[finfo["full_name"]]

    def _update_archive(self, finfo: dict):
        pass

    def run(self):
        """Главная функция. Запускаемся, читаем данные"""

        server = Client(self.cfg.ftp_server, download_dir=self.cfg.tmp_folder)

        count = 0  # FIXME: только для тестов
        for fdict in server.read():
            count += 1  # FIXME: только для тестов
            if self._has_archive(fdict):
                if self._need_to_update_archive(fdict):
                    server.download(fdict["full_name"], fdict["fname"])
                    self._update_archive(fdict)
                continue

            server.download(fdict["full_name"], fdict["fname"])
            fdict["id"] = self.db.add_archive(fdict["full_name"], fdict["fname"], fdict["fsize"])
            self._handle_archive(fdict)

            # FIXME: только для тестов
            if count >= 1:
                break


def run():
    log = get_logger(__name__)
    log.info("Init work")
    log.debug("Create instance of Application")

    app = _Application()
    log.debug("Run")
    app.run()
