
# -*- coding: utf-8 -*-

import os
import signal
from datetime import datetime as dt
from .log import get_logger
from .purchases import Client
from .db import DBClient
from .law.readers import FFLReaders
from .config import conf
from .util import get_archive_date
from .errors import EmptyValue


_ARCHIVE_EXISTS_BUT_NOT_PARSED = 1
_ARCHIVE_EXISTS_BUT_SIZE_DIFFERENT = 2
_NOTIFICATIONS_FOLDER = "notifications"
_PROTOCOLS_FOLDER = "protocols"


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
    """The main application class"""

    def __init__(self):
        self.log = get_logger(__name__)
        self.db = DBClient()
        self._archives = {}
        self._client = None

        self._check_tmp_folder()

        self._folder_name = conf("app.server_folder_name")
        self._law_number = conf("app.law_number")
        self.log.info(f"Server folder name is '{self._folder_name}'")

        self.killer = _GracefulKiller()
        self._ffl = FFLReaders(self.killer)
        if self._folder_name == _NOTIFICATIONS_FOLDER:
            self._ffl_reader = self._ffl.notifications
        else:
            self._ffl_reader = self._ffl.protocols

    def _check_tmp_folder(self):
        tmp_folder: str = conf("app.tmp_folder")
        if tmp_folder is None:
            raise EmptyValue("The value of 'tmp_folder' in config cannot be empty")
        elif not os.path.exists(tmp_folder):
            raise FileNotFoundError(tmp_folder)

    def _has_archive(self, finfo: dict) -> bool:
        """Checking, is there already information about this archive or no.

        Args:
            finfo (dict): A dict with archive data.

        Returns:
            bool: Result of checking.
        """

        # Look, what is there in DB about this file.
        # There can be situation, when an information about the file there is in DB and
        # this file was read and parsed, but metadata between this file and file from FTP are different.
        # In this case we should update data in DB.
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
        return finfo["full_name"] in self._archives

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
        """General method. Downloads, reads and handles archives"""

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
                self.db.update_archive(
                    archive_id,
                    reason="Archive was upload early, but not parsed",
                    updated_on=dt.utcnow()
                )
            elif need_to_update_archive_size:
                self.db.update_archive(
                    archive_id,
                    size=fdict["fsize"],
                    updated_on=dt.utcnow(),
                    reason="Archive was upload and parsed early, but current size of file is different"
                )

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
