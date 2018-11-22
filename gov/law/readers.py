
# -*- coding: utf-8 -*-

"""Модуль для работы с закупками по разным ФЗ
"""

from zipfile import ZipFile
from lxml import etree
from ..db import DBClient
from ..log import get_logger
from ..errors import WrongReaderLawError
from ..util import get_tag, recursive_dict


class FortyFourthLawNotifications():
    """Handler of 'notifications' folder of 44th law
    """

    __XML_TAGS = {}
    __XML_TYPES = ("fcsNotificationEF", "fcsClarification", "fcsPlacementResult")

    def __init__(self):
        self.log = get_logger(__name__)
        self.db = DBClient()
        self._register_tags()

    def _parse_xml(self, elem):
        (tag, elem_data) = recursive_dict(elem)
        return self.__XML_TAGS[tag], elem_data

    def _register_tags(self):
        """Register tags
        """
        self.log.debug("Fill tag aliases")
        self.__XML_TAGS = {
            "purchaseNumber": "purchase_number",
            "placingWay": "placing_way",
            "purchaseResponsible": "purchase_responsible",
            "ETP": "etp",
            "procedureInfo": "procedure_info",
            "lot": "lot",
            "purchaseObjectInfo": "purchase_object_info",
            "href": "href",
            "attachments": "attachments"
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
        """Parse XML file. If it is 44th law file, upload its to DB.

        Args:
            xml (bytes): Raw XML data.
            file_id (int): ID of row with file info from DB.
        """

        root = etree.fromstring(xml)
        file_data = {}

        first_element = root.iter()
        xml_type = get_tag(first_element)
        if xml_type not in self.__XML_TYPES:
            pass

        for elem in list(first_element):
            tag_name = get_tag(elem.tag)
            if tag_name in self.__XML_TAGS:
                field_key, field_value = self._parse_xml(elem)
                file_data[field_key] = field_value
            else:
                self.log.debug(f"There is no handler for {tag_name}. Skip it")

        if len(file_data) == 0:
            self.log.warn("There is no one knowledge tag in file")
            return

        self.log.debug(f"{file_data}")
        self.db.add_ffl_notification(file_id, file_data)
