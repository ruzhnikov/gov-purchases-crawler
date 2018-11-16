
# -*- coding: utf-8 -*-

"""Модуль для работы с закупками по разным ФЗ
"""

from zipfile import ZipFile
from lxml import etree
from ..db import DBClient
from ..log import get_logger
from ..utils import get_tag
from ..errors import WrongReaderLawError


FORTY_FORTH_LAW = 44
AVAILABLE_LAWS = (FORTY_FORTH_LAW,)


class _CommonHandler():
    """Класс с обработчиками для полей XML структур

    Raises:
        WrongReaderLawError: Если law не находится в списке AVAILABLE_LAWS.
    """

    def __init__(self, law):
        self.log = get_logger(__name__)
        if law not in AVAILABLE_LAWS:
            raise WrongReaderLawError(law)
        self._law = law
        self.db = DBClient()

    def purchase_number(self, elem, return_in_dict=False):
        """Обработчик для поля purchaseNumber

        Args:
            elem (lxml.etree.ElementBase): Элемент XML структуры.
            return_in_dict (bool, optional): Defaults to False. Не записывать данные в БД, просто вернуть в словаре.
        """
        self.log.info(f"Handle {get_tag(elem.tag)}")
        for e in elem.iter():
            self.log.info("{} => {}".format(get_tag(e.tag), e.text))

    def placing_way(self, elem):
        self.log.info(f"Handle {get_tag(elem.tag)}")
        for e in elem.iter():
            self.log.info(f"{get_tag(e.tag)} => {e.text}")

    def purchase_responsible(self, elem):
        self.log.info(f"Handle {get_tag(elem.tag)}")
        for e in elem.iter():
            self.log.info(f"{get_tag(e.tag)} => {e.text}")

    def etp(self, elem):
        self.log.info(f"Handle {get_tag(elem.tag)}")
        for e in elem.iter():
            self.log.info(f"{get_tag(e.tag)} => {e.text}")

    def procedure_info(self, elem):
        self.log.info(f"Handle {get_tag(elem.tag)}")
        for e in elem.iter():
            self.log.info(f"{get_tag(e.tag)} => {e.text}")

    def lot(self, elem):
        self.log.info(f"Handle {get_tag(elem.tag)}")
        for e in elem.iter():
            self.log.info(f"{get_tag(e.tag)} => {e.text}")


class FortyFourthLaw():
    """Обработчик для ФЗ44"""

    __HANDLERS = {}

    def __init__(self):
        self.log = get_logger(__name__)
        self.db = DBClient()
        self.h = _CommonHandler(FORTY_FORTH_LAW)
        self._register_handlers()

    def _register_handlers(self):
        self.log.debug("Register handlers")
        self.__HANDLERS = {
            "purchaseNumber": self.h.purchase_number,
            "placingWay": self.h.placing_way,
            "purchaseResponsible": self.h.purchase_responsible,
            "ETP": self.h.etp,
            "procedureInfo": self.h.procedure_info,
            "lot": self.h.lot
        }

    def handle_archive(self, archive: str, archive_id: int):
        """Обработка архива. Чтение, парсинг и запись в БД

        Args:
            archive (str): Имя файла с архивом.
        """

        for xml, file_info in self._read_archive(archive, archive_id):
            self._parse_and_upload_xml(xml, file_info)

    def _parse_and_upload_xml(self, xml, file_info: dict):
        root = etree.fromstring(xml)

        for attr in root.iter():
            for elem in attr.iter():
                tag_name = get_tag(elem.tag)
                if tag_name in self.__HANDLERS:
                    handler = self.__HANDLERS[tag_name]
                    if not callable(handler):
                        self.log.warning(f"The handler of key {tag_name} is not callable and will be skipped")
                        continue
                    handler(elem)

    def _read_archive(self, archive: str, archive_id: int):
        """Чтение архива. Возвращает генератор

        Args:
            archive (str): Имя файла с архивом.

        Yields:
            bytes: Данные из прочитанного XML файла.
            dict: Информация об XML файле, имя и размер.
        """
        with ZipFile(archive, "r") as zip:
            for entry in zip.infolist():
                if not entry.filename.endswith(".xml"):
                    continue
                if self.db.has_parsed_archive_file(archive_id, entry.filename, entry.file_size):
                    continue
                with zip.open(entry.filename, "r") as f:
                    xml = f.read()
                yield xml, {"fname": entry.filename, "fsize": entry.file_size}
