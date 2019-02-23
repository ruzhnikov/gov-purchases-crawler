
# -*- coding: utf-8 -*-

import os
import signal
from .log import get_logger
from .purchases import Client
from .db import DBClient
from .law.readers import FFLReaders
from .config import conf


_ARCHIVE_EXISTS_BUT_NOT_PARSED = 1
_ARCHIVE_EXISTS_BUT_SIZE_DIFFERENT = 2


class _GracefulKiller():
    """Handler of external signals"""

    kill_now = False

    def __init__(self):
        self.log = get_logger(__name__)
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self, signum, frame):
        self.log.info(f"Got signal {signum}; Try to finish work gracefully")
        self.kill_now = True


class _Application():

    def __init__(self):
        self.log = get_logger(__name__)
        self.db = DBClient()
        self._archives = {}

        cfg = conf("app")
        self._folder_name = cfg["server_folder_name"]
        self.log.info(f"Server folder name {self._folder_name}")

        self.killer = _GracefulKiller()
        self._ffl = FFLReaders(self.killer)
        self._ffl_reader = self._ffl.notifications if self._folder_name == "notifications" else self._ffl.protocols

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

    def _handle_archive(self, finfo: dict) -> bool:
        """Work with downloaded archive. After handling the file is removed.

        Args:
            finfo (dict): Information about archive file.

        Returns:
            bool: Work result. If True - all fine, otherwise - an error has been occured.
        """

        self.log.info(f"Archive file: {finfo['fname']}; Size: {finfo['fsize']}")
        cfg = conf("app")
        zip_file = cfg["tmp_folder"] + "/" + finfo["fname"]
        read_archive_result = self._ffl_reader.handle_archive(zip_file, finfo["id"])

        # clean after work
        if os.path.isfile(zip_file):
            self.log.debug(f"Remove file {zip_file}")
            os.remove(zip_file)

            self.log.debug("Clean archive info")
            if finfo["full_name"] in self._archives:
                del self._archives[finfo["full_name"]]

        return read_archive_result

    def run(self):
        """General method. Running, read and handle archives"""

        cfg = conf("app")
        server = Client(cfg["ftp_server"], download_dir=cfg["tmp_folder"], looking_folder=self._folder_name)

        # We can handle particular amount of archives.
        # This parameter is set by config.
        count = 0
        error_count = 0
        need_limit = cfg["limit_archives"] != 0
        limit = cfg["limit_archives"] if need_limit else None

        self.log.info(f"Limit is {limit}")

        for fdict in server.read():

            # got signal from system or user. Abort any actions.
            if self.killer.kill_now:
                self.log.info("Gracefully stop reading archives from server because of signal")
                break

            archive_id = None
            archive_has_updated = False

            if self._has_archive(fdict):
                # we already have this parsed archive. Just skip it.
                if not self._need_to_update_archive(fdict):
                    self.log.debug(f"The file {fdict['fname']} had been parsed early. Skip them.")
                    continue

                # we have non parsed archive or size of archive is different.
                # Anyway we should reparse archive again.
                archive = self.db.get_archive(fdict["fname"], fdict["fsize"])
                archive_id = archive.id
                self.log.info(f"Found archive wih ID {archive_id}")
                if self._need_to_clean_old_files(fdict):
                    self.db.delete_archive_files(archive_id)
                    archive_has_updated = True

            count += 1
            try:
                server.download(fdict["full_name"], fdict["fname"])
            except Exception as e:
                # TODO: here we should catch exception "time is over" and reconnect to server
                self.log.error(f"Error to download archive: {e}")
                error_count += 1
                self.log.info("Try to next iteration")
                continue

            if archive_id is None:
                archive_id = self.db.add_archive(
                    fname=fdict["fname"],
                    fsize=fdict["fsize"],
                    law_number=cfg["law_number"], folder_name=self._folder_name)

            fdict["id"] = archive_id
            if self._handle_archive(fdict) is False:
                error_count += 1
            elif archive_has_updated:
                # TODO: здесь нужно обновить size архива
                self.db.update_archive_size(archive_id, fdict["fsize"])

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
