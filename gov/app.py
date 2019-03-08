
# -*- coding: utf-8 -*-

import os
import signal
from .log import get_logger
from .purchases import Client
from .db import DBClient
from .law.readers import FFLReaders
from .config import conf
from .util import get_archive_date


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
        self._client = None

        self._folder_name = conf("app.server_folder_name")
        self._law_number = conf("app.law_number")
        self.log.info(f"Server folder name is '{self._folder_name}'")

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

    def _archive_was_not_parsed(self, finfo: dict) -> bool:
        key = finfo["full_name"]
        return key in self._archives and self._archives[key] == _ARCHIVE_EXISTS_BUT_NOT_PARSED

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

        self._client = Client(
            conf("app.ftp_server"),
            download_dir=conf("app.tmp_folder"),
            looking_folder=self._folder_name)

        has_limit, limit = self._get_limit()
        self.log.info(f"Limit of archives is {limit if limit is not None else 'Unlimited'}")
        count, error_count = self._read_from_client(has_limit, limit)

        self.log.info(f"Total were handled: {count} archive(s)")
        self.log.info(f"Total were obtained {error_count} errors")

    def _read_from_client(self, has_limit: bool, limit):
        count = error_count = 0

        for fdict in self._client.read():

            # got signal from system or user. Abort any actions.
            if self.killer.kill_now:
                self.log.info("Abort reading archives from server because of interrupt signal")
                break

            # invoke filters
            if self._skip_archive_by_region_filter(fdict["region"]):
                continue

            if self._skip_archive_by_date_filter(fdict['fname']):
                continue

            archive_id = None
            need_to_touch_archive = need_to_update_archive_size = False

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
                    need_to_update_archive_size = True
                elif self._archive_was_not_parsed(fdict):
                    need_to_touch_archive = True

            count += 1
            if not self._download(fdict):
                error_count += 1
                continue

            if archive_id is None:
                archive_id = self.db.add_archive(
                    fname=fdict["fname"],
                    fsize=fdict["fsize"],
                    law_number=self._law_number, folder_name=self._folder_name)

            fdict["id"] = archive_id
            if self._handle_archive(fdict) is False:
                error_count += 1
            elif need_to_touch_archive:
                self.db.touch_archive(archive_id)
            elif need_to_update_archive_size:
                self.db.update_archive_size(archive_id, fdict["fsize"])

            if has_limit and count >= limit:
                break

        return count, error_count

    def _download(self, finfo: dict) -> bool:
        try:
            self._client.download(finfo["full_name"], finfo["fname"])
        except Exception as e:
            # TODO: here we should catch exception "time is over" and reconnect to server
            self.log.error(f"Error to download archive: {e}")
            self.log.info("Try to next iteration")
            return False

        return True

    def _get_limit(self):
        limit = conf("app.limit_archives")
        has_limit = limit != 0
        if not has_limit:
            limit = None

        return has_limit, limit

    def _skip_archive_by_region_filter(self, region) -> bool:
        f = conf("app.filters")

        if f.has_region_filter:
            if f.filter_region(region) and f.is_positive_region_match:
                return False
            elif not f.filter_region(region) and f.is_negative_region_match:
                return False
            else:
                self.log.info(f"Skip region {region} due to region filter")
                self._client.set_region_skipped(region)
                return True

        return False

    def _skip_archive_by_date_filter(self, archive_name: str) -> bool:
        f = conf("app.filters")

        if f.has_date_filter:
            date, error = get_archive_date(archive_name)
            if error is not None:
                self.log.error(f"Got error during parse name of archive: {error}")
                return False

            if f.filter_date(date) and f.is_positive_date_match:
                return False
            elif not f.filter_date(date) and f.is_negative_date_match:
                return False
            else:
                self.log.info(f"Skip the archive {archive_name} due to date filter")
                return True

        return False


def run():
    log = get_logger(__name__)
    log.info("Init work")
    log.debug("Create instance of Application")

    app = _Application()
    log.debug("Run")
    app.run()
    log.info("End of work")
