
# -*- coding: utf-8 -*-

"""A module for working with purchases over different laws.
"""

from zipfile import ZipFile
from lxml import etree
from ..db import FortyFourthLawDB
from ..log import get_logger
from . import get_tag, recursive_dict, remove_signature


class FortyFourthLawNotifications():
    """Handler of 'notifications' folder of 44th law
    """

    __OFTEN_TAGS = {}
    __RARE_TAGS = {}
    __TAG_HANDLERS = {}

    def __init__(self):
        self.log = get_logger(__name__)
        self.db = FortyFourthLawDB()
        self._register_tags()

    def _parse_tag_data(self, elem, tags_dict: dict, handler=None):
        (tag, elem_data) = recursive_dict(elem)
        if handler is None:
            return tags_dict[tag], elem_data
        elif callable(handler):
            return tags_dict[tag], handler(elem_data)
        else:
            self.log.warning(f"Wrong format of handler {handler}. Handler must be function")
            return tags_dict[tag], elem_data

    def _register_tags(self):
        """Register tags
        """
        self.log.debug("Fill tag aliases")

        self.__OFTEN_TAGS = {k: v for (k, v) in self.db.get_columns_dict(self.db.often_tags_table)}
        self.__RARE_TAGS = {k: v for (k, v) in self.db.get_columns_dict(self.db.rare_tags_table)}
        self.__TAG_HANDLERS = {
            "printForm": remove_signature
        }

        self.log.debug("Done")

    def handle_archive(self, archive: str, archive_id: int):
        """Обработка архива. Чтение, парсинг и запись в БД

        Args:
            archive (str): Имя файла с архивом.
            archive_id (int): ID архива в БД.
        """

        with ZipFile(archive, "r") as zip:
            for entry in zip.infolist():
                if not entry.filename.endswith(".xml"):
                    continue
                # if self.db.has_parsed_archive_file(archive_id, entry.filename, entry.file_size):
                #     already_have_file = True
                #     continue
                with zip.open(entry.filename, "r") as f:
                    xml = f.read()
                file_id = self.db.add_archive_file(archive_id, entry.filename, entry.file_size)
                self._parse_and_upload_xml(xml, file_id)
        self.db.mark_archive_as_parsed(archive_id)

    def _parse_and_upload_xml(self, xml: bytes, file_id: int):
        """Parse XML file. Upload its data to DB.

        Args:
            xml (bytes): Raw XML data.
            file_id (int): ID of row with file info from DB.
        """

        root = etree.fromstring(xml)
        (often_data, rare_data) = ({}, {})
        unknown_data = []
        reason = None

        first_element = list(root)[0]
        xml_type = get_tag(first_element)

        for elem in list(first_element):
            tag_name = get_tag(elem.tag)
            tags_dict = None
            handler = None
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

            if tag_name in self.__TAG_HANDLERS:
                handler = self.__TAG_HANDLERS[tag_name]

            data_key, data_value = self._parse_tag_data(elem, tags_dict, handler)
            if isinstance(local_data_storage, dict):
                local_data_storage[data_key] = data_value
            else:
                local_data_storage.append((data_key, data_value))

        if len(often_data) == 0 and len(rare_data) == 0 and len(unknown_data) == 0:
            reason = "There is no one knowledge or unknown tag in file"
            self.log.warn(reason)
            self.db.mark_archive_file_as_parsed(file_id, xml_type=xml_type, reason=reason)
            return

        session = self.db.session()
        if len(often_data):
            often_data["archive_file_id"] = file_id
            data = self.db.often_tags_table(**often_data)
            session.add(data)

        if len(rare_data):
            rare_data["archive_file_id"] = file_id
            data = self.db.rare_tags_table(**rare_data)
            session.add(data)

        for local_data in unknown_data:
            data = self.db.unknown_tags_table(archive_file_id=file_id, name=local_data[0], value=local_data[1])
            session.add(data)

        self.db.mark_archive_file_as_parsed(file_id, xml_type, session)
        session.commit()
