
# -*- coding: utf-8 -*-

"""A module for working with purchases over different laws.
"""

from zipfile import ZipFile
from lxml import etree
from ..db import FortyFourthLawDB
from ..log import get_logger
from . import util


_FILE_EXISTS_BUT_NOT_PARSED = 1
_FILE_EXISTS_BUT_SIZE_DIFFERENT = 2
_REASONS = {
    _FILE_EXISTS_BUT_NOT_PARSED: "File was upload early, but not parsed yet",
    _FILE_EXISTS_BUT_SIZE_DIFFERENT: "File was upload and parsed early, but current size of file is different"
}


class FortyFourthLawNotifications():
    """Handler of 'notifications' folder of 44th law
    """

    __OFTEN_TAGS = {}
    __RARE_TAGS = {}
    __TAG_HANDLERS = {}
    __SKIP_TAGS = ()

    def __init__(self):
        self.log = get_logger(__name__)
        self.db = FortyFourthLawDB()
        self._register_tags()
        self._files = {}

    def _parse_tag_data(self, elem, tags_dict: dict) -> tuple:
        tag, elem_data = util.recursive_read_dict(elem, skip_tags=self.__SKIP_TAGS, tag_handlers=self.__TAG_HANDLERS)
        return tags_dict[tag], elem_data

    def _register_tags(self):
        """Register tags
        """
        self.log.debug("Fill tag aliases")

        self.__OFTEN_TAGS = {k: v for (k, v) in self.db.get_columns_dict(self.db.notifications.often_tags_table)}
        self.__RARE_TAGS = {k: v for (k, v) in self.db.get_columns_dict(self.db.notifications.rare_tags_table)}
        self.__SKIP_TAGS = ("cryptoSigns", "signature")

        self.log.debug("Done")

    def handle_archive(self, archive: str, archive_id: int):
        """Обработка архива. Чтение, парсинг и запись в БД

        Args:
            archive (str): Имя файла с архивом.
            archive_id (int): ID архива в БД.
        """

        has_wrong_files = False
        with ZipFile(archive, "r") as zip_file:
            for entry in zip_file.infolist():
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
                        self.log.debug(f"The file {fname} had been parsed early. Skip them.")
                        continue

                    need_to_update = True

                # read and handle file
                with zip_file.open(fname, "r") as f:
                    xml = f.read()

                if need_to_update:
                    file = self.db.get_archive_file(archive_id, fname, fsize)
                    file_id = file.id
                    reason = self._files[fname]

                    # we should clean old tags of file
                    if reason == _FILE_EXISTS_BUT_SIZE_DIFFERENT:
                        self.db.delete_file_tags(file_id)
                    reason = _REASONS[reason]
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

        if has_wrong_files:
            self.log.warning(
                f"One or more file(s) of archive {archive_id} weren't parsed. Archive is not marked as parsed")
        else:
            self.db.mark_archive_as_parsed(archive_id)

    def _has_archive_file(self, archive_id: int, fname: str, fsize: int) -> bool:
        file_status = self.db.get_archive_file_status(archive_id, fname, fsize)
        if file_status == self.db.FILE_STATUS["FILE_DOES_NOT_EXIST"]:
            return False
        elif file_status == self.db.FILE_STATUS["FILE_EXISTS"]:
            return True
        elif file_status == self.db.FILE_STATUS["FILE_EXISTS_BUT_NOT_PARSED"]:
            self._files[fname] = _FILE_EXISTS_BUT_NOT_PARSED
            return True
        elif file_status == self.db.FILE_STATUS["FILE_EXISTS_BUT_SIZE_DIFFERENT"]:
            self._files[fname] = _FILE_EXISTS_BUT_SIZE_DIFFERENT
            return True

        return False

    def _need_to_update_file(self, fname: str) -> bool:
        if fname not in self._files:
            return False

        return True

    def _parse_and_upload_xml(self, xml: bytes, file_id: int, reason=None):
        """Parse XML file. Upload its data to DB.

        Args:
            xml (bytes): Raw XML file data.
            file_id (int): ID of row with file info from DB.
            reason (str, optional): Defaults to None. Field 'reason' for saving in DB.
        """

        root = etree.fromstring(xml)
        (often_data, rare_data) = ({}, {})
        unknown_data = []
        reason = reason if reason is not None else "OK"

        first_element = list(root)[0]
        xml_type = util.get_tag(first_element)

        for elem in list(first_element):
            tag_name = util.get_tag(elem.tag)
            tags_dict = None
            local_data_storage = None

            if tag_name in self.__OFTEN_TAGS:
                tags_dict = self.__OFTEN_TAGS
                local_data_storage = often_data
            elif tag_name in self.__RARE_TAGS:
                tags_dict = self.__RARE_TAGS
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

        if len(often_data) == 0 and len(rare_data) == 0 and len(unknown_data) == 0:
            self.log.warn(reason)
            self.db.mark_archive_file_as_parsed(file_id, xml_type=xml_type,
                                                reason="There is no one knowledge or unknown tag in file")
            return

        # we should save all changes by one transaction.
        session = self.db.session()
        if len(often_data):
            often_data["archive_file_id"] = file_id
            data = self.db.notifications.often_tags_table(**often_data)
            session.add(data)

        if len(rare_data):
            rare_data["archive_file_id"] = file_id
            data = self.db.notifications.rare_tags_table(**rare_data)
            session.add(data)

        for local_data in unknown_data:
            data = self.db.notifications.unknown_tags_table(
                archive_file_id=file_id, name=local_data[0], value=local_data[1])
            session.add(data)

        self.db.mark_archive_file_as_parsed(file_id, xml_type, reason=reason, session=session)
        session.commit()
        session.close()
