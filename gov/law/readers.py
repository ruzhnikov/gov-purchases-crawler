
# -*- coding: utf-8 -*-

"""Модуль для работы с закупками по разным ФЗ
"""

from zipfile import ZipFile
from lxml import etree
from ..log import get_logger
from ..utils import get_tag
from ..errors import WrongReaderLawError


_FORTY_FORTH_LAW = 44
_AVAIL_LAWS = (_FORTY_FORTH_LAW,)


class _CommonHandler():
    """Класс с обработчиками для полей XML структур

    Raises:
        WrongReaderLawError: если law не находится в списке _AVAIL_LAWS
    """

    def __init__(self, law):
        self.log = get_logger(__name__)
        if law not in _AVAIL_LAWS:
            raise WrongReaderLawError(law)
        self._law = law

    def purchase_number(self, elem, return_in_dict=False):
        """Обработчик для поля purchaseNumber

        Args:
            elem (lxml.etree.ElementBase): элемент XML структуры
            return_in_dict (bool, optional): Defaults to False. Не записывать данные в БД, просто вернуть в словаре
        """
        self.log.info("Handle {}".format(get_tag(elem.tag)))
        for e in elem.iter():
            self.log.info("{} => {}".format(get_tag(e.tag), e.text))

    def placing_way(self, elem):
        self.log.info("Handle {}".format(get_tag(elem.tag)))
        for e in elem.iter():
            self.log.info("{} => {}".format(get_tag(e.tag), e.text))

    def purchase_responsible(self, elem):
        self.log.info("Handle {}".format(get_tag(elem.tag)))
        for e in elem.iter():
            self.log.info("{} => {}".format(get_tag(e.tag), e.text))

    def etp(self, elem):
        self.log.info("Handle {}".format(get_tag(elem.tag)))
        for e in elem.iter():
            self.log.info("{} => {}".format(get_tag(e.tag), e.text))

    def procedure_info(self, elem):
        self.log.info("Handle {}".format(get_tag(elem.tag)))
        for e in elem.iter():
            self.log.info("{} => {}".format(get_tag(e.tag), e.text))

    def lot(self, elem):
        self.log.info("Handle {}".format(get_tag(elem.tag)))
        for e in elem.iter():
            self.log.info("{} => {}".format(get_tag(e.tag), e.text))


class FortyFourthLaw():
    """Обработчик для ФЗ44"""

    __HANDLERS = {}

    def __init__(self):
        self.log = get_logger(__name__)
        self.h = _CommonHandler(_FORTY_FORTH_LAW)
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

    def handle_archive(self, archive):
        """Обработка архива. Чтение, парсинг и запись в БД

        Args:
            archive (str): имя файла с архивом
        """
        for xml in self._read_archive(archive):
            self._parse_and_upload_xml(xml)

    def _parse_and_upload_xml(self, xml):
        root = etree.fromstring(xml)

        for attr in root.iter():
            for elem in attr.iter():
                tag_name = get_tag(elem.tag)
                if tag_name in self.__HANDLERS:
                    handler = self.__HANDLERS[tag_name]
                    if not callable(handler):
                        self.log.warning("The handler of key {} is not callable and will be skipped".format(tag_name))
                        continue
                    handler(elem)

    def _read_archive(self, archive):
        """Чтение архива. Возвращает генератор

        Args:
            archive (str): Файл с архивом.

        Yields:
            bytes: Данные из прочитанного XML файла.
        """
        with ZipFile(archive, "r") as zip:
            for entry in zip.namelist():
                if not entry.endswith(".xml"):
                    continue
                with zip.open(entry, "r") as f:
                    xml = f.read()
                yield xml
