
# -*- coding: utf-8 -*-

from zipfile import ZipFile
from lxml import etree
from ..db import FortyFourthLawDB
from ..log import get_logger
from . import util
from . import _REASONS, _REASON_CODES


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

    def _register_tags(self, db_namespace):
        """Register tags in local storage"""

        self.log.debug("Fill tag aliases")
        self._OFTEN_TAGS = {k: v for (k, v) in self.db.get_columns_dict(db_namespace.often_tags_table)}
        self._RARE_TAGS = {k: v for (k, v) in self.db.get_columns_dict(db_namespace.rare_tags_table)}
        self.log.debug("Done")

    def _parse_tag_data(self, elem, tags_dict: dict) -> tuple:
        tag, elem_data = util.recursive_read_dict(elem, skip_tags=self._SKIP_TAGS, tag_handlers=self._TAG_HANDLERS)
        return tags_dict[tag], elem_data

    def _has_archive_file(self, archive_id: int, fname: str, fsize: int) -> bool:
        file_status = self.db.get_archive_file_status(archive_id, fname, fsize)
        if file_status == self.db.FILE_STATUS["FILE_DOES_NOT_EXIST"]:
            return False
        elif file_status == self.db.FILE_STATUS["FILE_EXISTS"]:
            return True
        elif file_status == self.db.FILE_STATUS["FILE_EXISTS_BUT_NOT_PARSED"]:
            self._files[fname] = _REASON_CODES["FILE_EXISTS_BUT_NOT_PARSED"]
            return True
        elif file_status == self.db.FILE_STATUS["FILE_EXISTS_BUT_SIZE_DIFFERENT"]:
            self._files[fname] = _REASON_CODES["FILE_EXISTS_BUT_SIZE_DIFFERENT"]
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
        with ZipFile(archive, "r") as zip_file:
            for entry in zip_file.infolist():
                if self.killer.kill_now:
                    has_killed = True
                    break

                if not entry.filename.endswith(".xml"):
                    continue

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

                    # we should clean old tags of file
                    if reason_code == _REASON_CODES["FILE_EXISTS_BUT_SIZE_DIFFERENT"]:
                        self.db.delete_file_tags(file_id)
                    reason = _REASONS[reason_code]
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
            return False
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
        first_element = list(root)[0]
        xml_type = util.get_tag(first_element)

        reason = reason if reason is not None else "OK"
        (often_data, rare_data, unknown_data) = self._read_xml_root(first_element)

        if len(often_data) == 0 and len(rare_data) == 0 and len(unknown_data) == 0:
            self.log.warn(reason)
            self.db.mark_archive_file_as_parsed(file_id, xml_type=xml_type,
                                                reason="There is no one knowledge or unknown tag in file")
            return

        # we should save all changes by one transaction.
        session = self.db.session()
        if len(often_data):
            often_data["archive_file_id"] = file_id
            data = self._db_namespace.often_tags_table(**often_data)
            session.add(data)

        if len(rare_data):
            rare_data["archive_file_id"] = file_id
            data = self._db_namespace.rare_tags_table(**rare_data)
            session.add(data)

        for local_data in unknown_data:
            data = self._db_namespace.unknown_tags_table(
                archive_file_id=file_id, name=local_data[0], value=local_data[1])
            session.add(data)

        self.db.mark_archive_file_as_parsed(file_id, xml_type, reason=reason, session=session)
        session.commit()
        session.close()

    def _read_xml_root(self, first_element) -> (dict, dict, list):
        """Read and parse XML elements that are children of root element(first_element)

        Args:
            first_element (etree._Element): Root element.
        """

        (often_data, rare_data) = ({}, {})
        unknown_data = []

        for elem in list(first_element):
            tag_name = util.get_tag(elem.tag)
            tags_dict = None
            local_data_storage = None

            if tag_name in self._OFTEN_TAGS:
                tags_dict = self._OFTEN_TAGS
                local_data_storage = often_data
            elif tag_name in self._RARE_TAGS:
                tags_dict = self._RARE_TAGS
                local_data_storage = rare_data
            else:
                self.log.warning(f"Unknown element {tag_name}")
                tags_dict = {tag_name: tag_name}
                local_data_storage = unknown_data

            data_key, data_value = self._parse_tag_data(elem, tags_dict)
            if isinstance(local_data_storage, dict):
                local_data_storage[data_key] = data_value
            else:
                local_data_storage.append((data_key, data_value))

        return often_data, rare_data, unknown_data


class FortyFourthLawNotifications(_FortyFourthLawBase):
    """Handler of `notifications` folder of 44th law
    """

    _TAG_HANDLERS = {}
    _SKIP_TAGS = ("cryptoSigns", "signature")

    def __init__(self):
        super().__init__()
        self._db_namespace = self.db.notifications
        self._register_tags(self._db_namespace)


class FortyFourthLawProtocols(_FortyFourthLawBase):
    """Handler of `protocols` folder of 44th law"""

    _TAG_HANDLERS = {}
    _SKIP_TAGS = ("cryptoSigns", "signature")

    def __init__(self):
        super().__init__()
        self._db_namespace = self.db.protocols
        self._register_tags(self._db_namespace)
