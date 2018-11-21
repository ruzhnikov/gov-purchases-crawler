
# -*- coding: utf-8 -*-

"""Модуль для работы с закупками по разным ФЗ
"""

from zipfile import ZipFile
from lxml import etree
from ..db import DBClient
from ..log import get_logger
from ..errors import WrongReaderLawError
from ..util import get_tag, recursive_dict


FORTY_FORTH_LAW = 44
AVAILABLE_LAWS = (FORTY_FORTH_LAW,)


class FortyFourthLaw():
    """Обработчик для ФЗ44"""

    __XML_TAGS = {}

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
        self.log.info("Fill tag aliases")
        self.__XML_TAGS = {
            "purchaseNumber": "purchase_number",
            "placingWay": "placing_way",
            "purchaseResponsible": "purchase_responsible",
            "ETP": "etp",
            "procedureInfo": "procedure_info",
            "lot": "lot",
            "purchaseObjectInfo": "purchase_object_info",
            "href": "href"
        }

    def handle_archive(self, archive: str, archive_id: int):
        """Обработка архива. Чтение, парсинг и запись в БД

        Args:
            archive (str): Имя файла с архивом.
            archive_id (int): ID архива в БД.
        """

        for xml, file_info, already_have_file in self._read_archive(archive, archive_id):
            if already_have_file:
                continue
            file_id = self.db.add_archive_file(archive_id, file_info["fname"], file_info["fsize"])
            self._parse_and_upload_xml(xml, file_id)
        self.db.mark_archive_as_parsed(archive_id)

    def _parse_and_upload_xml(self, xml, file_id: int):
        root = etree.fromstring(xml)
        file_data = {}

        for attr in list(root):
            for elem in list(attr):
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

    def _read_archive(self, archive: str, archive_id: int):
        """Чтение архива. Возвращает генератор

        Args:
            archive (str): Имя файла с архивом.

        Yields:
            bytes: Данные из прочитанного XML файла.
            dict: Информация об XML файле, имя и размер.
            bool: Признак того, что файл уже был ранее прочитан и разобран.
        """
        with ZipFile(archive, "r") as zip:
            for entry in zip.infolist():
                already_have_file = False
                if not entry.filename.endswith(".xml"):
                    continue
                # if self.db.has_parsed_archive_file(archive_id, entry.filename, entry.file_size):
                #     already_have_file = True
                #     continue
                with zip.open(entry.filename, "r") as f:
                    xml = f.read()
                yield xml, {"fname": entry.filename, "fsize": entry.file_size}, already_have_file
