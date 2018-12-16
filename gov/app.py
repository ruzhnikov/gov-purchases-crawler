
# -*- coding: utf-8 -*-

import os
from .log import get_logger
from .purchases import Client
from .db import DBClient
from .law.readers import FortyFourthLawNotifications
from .config import AppConfig


_ARCHIVE_EXISTS_BUT_NOT_PARSED = 1
_ARCHIVE_EXISTS_BUT_SIZE_DIFFERENT = 2


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

        # Смотрим, что у нас в БД по этому файлу. Может быть ситуация, что файл в БД имеется и он
        # был прочитан и распарсен, но метаданные между ним и файлом с FTP сервера отличаются.
        # В таком случае нам нужно обновить данные в БД.
        arch_status = self.db.get_archive_status(finfo["fname"], finfo["fsize"])

        if arch_status == self.db.FILE_STATUS["FILE_DOES_NOT_EXIST"]:
            return False
        elif arch_status == self.db.FILE_STATUS["FILE_EXISTS"]:
            return True
        elif arch_status == self.db.FILE_STATUS["FILE_EXISTS_BUT_NOT_PARSED"]:
            self._archives[finfo["full_name"]] = _ARCHIVE_EXISTS_BUT_NOT_PARSED
            return True
        elif arch_status == self.db.FILE_STATUS["FILE_EXISTS_BUT_SIZE_DIFFERENT"]:
            self._archives[finfo["full_name"]] = _ARCHIVE_EXISTS_BUT_SIZE_DIFFERENT
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
            return False

        return True

    def _need_to_clean_old_files(self, finfo: dict) -> bool:
        key = finfo["full_name"]
        return key in self._archives and self._archives[key] == _ARCHIVE_EXISTS_BUT_SIZE_DIFFERENT

    def _handle_archive(self, finfo: dict):
        """Работа со скачанным файлом. После обработки файл удаляется

        Args:
            finfo (dict): Кортеж с данными о файле.
        """

        self.log.info(f"File: {finfo['fname']}; Size: {finfo['fsize']}")
        zip_file = self.cfg.tmp_folder + "/" + finfo["fname"]
        self.ffl.handle_archive(zip_file, finfo["id"])

        # clean after work
        if os.path.isfile(zip_file):
            self.log.debug(f"Remove file {zip_file}")
            os.remove(zip_file)

            self.log.debug("Clean archive info")
            if finfo["full_name"] in self._archives:
                del self._archives[finfo["full_name"]]

    def run(self):
        """General method. Running, read and handle archives"""

        server = Client(self.cfg.ftp_server, download_dir=self.cfg.tmp_folder)

        # We can handle particular amount of archives.
        # This parameter is set by config.
        count = 0
        error_count = 0
        need_limit = self.cfg.limit_archives is not None
        limit = self.cfg.limit_archives if need_limit else None

        self.log.info(f"Limit is {limit}")

        for fdict in server.read():
            if need_limit and limit == 0:
                break

            archive_id = None

            if self._has_archive(fdict):
                # we already have this parsed archive. Just skip it.
                if not self._need_to_update_archive(fdict):
                    self.log.debug(f"The file {fdict['fname']} had been parsed early. Skip them.")
                    continue

                # we have non parsed archive or size of archive is different. Anyway we should
                # reparse archive again.
                archive = self.db.get_archive(fdict["fname"], fdict["fsize"])
                archive_id = archive.id
                if self._need_to_clean_old_files(fdict):
                    self.db.delete_archive_files(archive_id)

            count += 1
            try:
                server.download(fdict["full_name"], fdict["fname"])
            except Exception as e:
                # TODO: here we should catch exception of "time is over" and reconnect to server
                self.log.error(f"Error to download archive: {e}")
                error_count += 1
                self.log.info("Try to next iteration")
                continue

            if archive_id is None:
                archive_id = self.db.add_archive(fname=fdict["fname"], fsize=fdict["fsize"])

            fdict["id"] = archive_id
            self._handle_archive(fdict)

            if need_limit and count >= limit:
                break

        self.log.info(f"Total were handled: {count} archive(s)")
        self.log.info(f"Total were obtained {error_count} errors")


def run():
    log = get_logger(__name__)
    log.info("Init work")
    log.debug("Create instance of Application")

    app = _Application()
    log.debug("Run")
    app.run()
    log.info("End of work")
