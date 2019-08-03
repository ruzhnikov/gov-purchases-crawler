
# -*- coding: utf-8 -*-

from zipfile import ZipFile
from lxml import etree
from ..db import FortyFourthLawDB
from ..db import FileStatus as DBFileStatus
from ..log import get_logger
from . import util
from ._reasons import Reason, ReasonCode, get_reason_by_code


_DEFAULT_REASON = "OK"


class _FortyFourthLawBase():
    """The base class for 44th law readers"""

    _TAG_HANDLERS = {}
    _SKIP_TAGS = ()

    def __init__(self):
        self.log = get_logger(__name__)
        self.db = FortyFourthLawDB()
        self._files = {}
        self._db_namespace = None

    def set_killer(self, killer):
        self.killer = killer

    def _has_archive_file(self, archive_id: int, fname: str, fsize: int) -> bool:
        file_status = self.db.get_archive_file_status(archive_id, fname, fsize)

        if file_status == DBFileStatus.FILE_DOES_NOT_EXIST:
            return False
        elif file_status == DBFileStatus.FILE_EXISTS:
            return True
        elif file_status == DBFileStatus.FILE_EXISTS_BUT_NOT_PARSED:
            self._files[fname] = ReasonCode.FILE_EXISTS_BUT_NOT_PARSED
            return True
        elif file_status == DBFileStatus.FILE_EXISTS_BUT_SIZE_DIFFERENT:
            self._files[fname] = ReasonCode.FILE_EXISTS_BUT_SIZE_DIFFERENT
            return True

        return False

    def _need_to_update_file(self, fname: str) -> bool:
        if fname not in self._files:
            return False

        return True

    def handle_archive(self, archive: str, archive_id: int):
        """Handling of archive. Read, parse and write to DB

        Args:
            archive (str): Name of archive file.
            archive_id (int): ID of archive in DB.
        """

        has_wrong_files = False
        has_killed = False
        files_counter = 0
        with ZipFile(archive, "r") as zip_file:
            for entry in zip_file.infolist():
                if self.killer.kill_now:
                    has_killed = True
                    break

                if not entry.filename.endswith(".xml"):
                    continue

                files_counter += 1
                fname = entry.filename
                fsize = entry.file_size

                # check existing of file
                need_to_update = False
                reason = None
                if self._has_archive_file(archive_id, fname, fsize):
                    # we already have this parsed file. Just skip it.
                    if not self._need_to_update_file(fname):
                        self.log.debug(f"The file {fname} had been parsed early. Skip it.")
                        continue

                    need_to_update = True

                # read and handle file
                with zip_file.open(fname, "r") as f:
                    xml = f.read()

                if need_to_update:
                    file = self.db.get_archive_file(archive_id, fname, fsize)
                    file_id = file.id
                    reason_code = self._files[fname]

                    if reason_code == ReasonCode.FILE_EXISTS_BUT_SIZE_DIFFERENT:
                        self.db.delete_file_data(file_id)
                    reason = get_reason_by_code(reason_code)
                else:
                    file_id = self.db.add_archive_file(archive_id, fname, fsize)

                self.log.info(f"Parse XML file {fname}")
                try:
                    self._parse_and_upload_xml(xml, file_id, reason)
                except Exception as e:
                    self.log.error(f"Got exception during parse file {fname}: {e}")
                    has_wrong_files = True

                if fname in self._files:
                    del self._files[fname]

        if has_killed:
            self.log.info("Gracefully stop reading archive because of signal")
            return True
        elif has_wrong_files:
            self.log.warning(
                f"One or more file(s) of archive {archive_id} weren't parsed. Archive is not marked as parsed")
            self.db.update_archive(archive_id, reason="One or more file(s) of archive weren't parsed")
            return False
        elif files_counter == 0:
            self.log.info("There is not one XML file in the archive")
            self.db.update_archive(archive_id, reason="Archive is empty")
        else:
            self.db.mark_archive_as_parsed(archive_id)
            return True

    def _parse_and_upload_xml(self, xml: bytes, file_id: int, reason=None):
        """Parse XML file. Upload its data to DB.

        Args:
            xml (bytes): Raw XML file data.
            file_id (int): ID of row with file info from DB.
            reason (str, optional): Defaults to None. Field 'reason' for saving in DB.
        """

        root = etree.fromstring(xml)
        root_element = list(root)[0]
        xml_type = util.get_tag(root_element)
        _, file_data = util.recursive_read_dict(root, skip_tags=self._SKIP_TAGS, tag_handlers=self._TAG_HANDLERS)

        reason = reason if reason is not None else "OK"

        if len(file_data) == 0:
            self.log.warn(reason)
            self.db.mark_archive_file_as_parsed(file_id, xml_type=xml_type,
                                                reason="There is no valid XML data in the file")
            return

        # we should save all changes by one transaction.
        session = self.db.get_session()
        self._insert_data(file_id, file_data, session)
        self.db.mark_archive_file_as_parsed(file_id, xml_type, reason=reason, session=session)
        session.commit()
        session.close()

    def _insert_data(self, *args):
        raise NotImplementedError(f"It has to be implemeted in {self.__class__.__name__}")


class FortyFourthLawNotifications(_FortyFourthLawBase):
    """Handler of `notifications` folder of 44th law
    """

    _TAG_HANDLERS = {}
    _SKIP_TAGS = ("cryptoSigns", "signature")

    def _insert_data(self, *args):
        self.db.insert_notification_data(*args)


class FortyFourthLawProtocols(_FortyFourthLawBase):
    """Handler of `protocols` folder of 44th law"""

    _TAG_HANDLERS = {}
    _SKIP_TAGS = ("cryptoSigns", "signature")

    def _insert_data(self, *args):
        self.db.insert_protocol_data(*args)
