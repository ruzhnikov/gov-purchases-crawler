
# -*- coding: utf-8 -*-

"""Модуль для работы с закупками по разным ФЗ
"""

from zipfile import ZipFile
from lxml import etree
from ..db import DBClient
from ..log import get_logger
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
        self.get_tag = lambda tag: etree.QName(tag).localname

    def purchase_number(self, elem, return_in_dict=False):
        """Обработчик для поля purchaseNumber

        Args:
            elem (lxml.etree.ElementBase): Элемент XML структуры.
            return_in_dict (bool, optional): Defaults to False. Не записывать данные в БД, просто вернуть в словаре.
        """
        self.log.info(f"Handle {self.get_tag(elem.tag)}")
        # for e in elem.iter():
        #     self.log.info(f"{self.get_tag(e.tag)} => {e.text}")

        return "purchase_number", elem.text

    def placing_way(self, elem):
        self.log.info(f"Handle {self.get_tag(elem.tag)}")
        # for e in elem.iter():
        #     self.log.info(f"{self.get_tag(e.tag)} => {e.text}")

        return "placing_way", {}

    def purchase_responsible(self, elem):
        self.log.info(f"Handle {self.get_tag(elem.tag)}")
        for e in elem.iter():
            self.log.info(f"{self.get_tag(e.tag)} => {e.text}")

        return "purchase_responsible", {}

    def etp(self, elem):
        self.log.info(f"Handle {self.get_tag(elem.tag)}")
        data = {}
        for e in list(elem):
            tag = self.get_tag(e.tag)
            data[tag] = e.text
        return "etp", data

    def procedure_info(self, elem):
        self.log.info(f"Handle {self.get_tag(elem.tag)}")
        # for e in elem.iter():
        #     self.log.info(f"{self.get_tag(e.tag)} => {e.text}")
        return "procedure_info", {}

    def lot(self, elem):
        self.log.info(f"Handle {self.get_tag(elem.tag)}")
        # for e in elem.iter():
        #     self.log.info(f"{self.get_tag(e.tag)} => {e.text}")
        return "lot", {}

    def href(self, elem):
        self.log.info(f"Handle {self.get_tag(elem.tag)}")
        return "href", elem.text

    def purchase_object_info(self, elem):
        self.log.info(f"Handle {self.get_tag(elem.tag)}")
        return "purchase_object_info", elem.text


class FortyFourthLaw():
    """Обработчик для ФЗ44"""

    # хранилище для обработчиков тэгов. Задаётся дальше.
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
            "lot": self.h.lot,
            "purchaseObjectInfo": self.h.purchase_object_info,
            "href": self.h.href
        }
        self.log.debug("Handler were registered")

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
                tag_name = self.h.get_tag(elem.tag)
                if tag_name in self.__HANDLERS:
                    handler = self.__HANDLERS[tag_name]
                    if not callable(handler):
                        self.log.warning(f"A handler of tag {tag_name} is not callable and its will be skipped")
                        continue
                    self.log.debug(f"A handler for tag {tag_name} was found. Call it")
                    field_key, field_value = handler(elem)
                    file_data[field_key] = field_value
                else:
                    self.log.debug(f"There is no handler for {tag_name}. Skip it")

        if len(file_data) == 0:
            self.log.warn("There is no one knowledge tag in file")
            return

        self.log.debug(f"{file_data}")
        self.db.add_ffl_content(file_id, file_data)

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
