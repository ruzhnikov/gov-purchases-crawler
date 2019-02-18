
# -*- coding: utf-8 -*-


class Error(Exception):
    """Base class for exceptions in this module."""
    pass


class WrongReaderLawError(Error):
    """Передан некорректный номер закона

    Args:
        law (int): Номер закона.

    Attributes:
        message (str): Сообщение об ошибке.
        law (int): Номер закона.
    """

    def __init__(self, law):
        self.message = "Wrong law {}".format(law)
        self.law = law


class EmptyDownloadDirError(Error):
    """Отсутствует папка для скачивания файла.
    Папка не была задана при создании объекта и не была передана при вызове метода.

    Attributes:
        message (str): Сообщение об ошибке.
    """

    def __init__(self):
        self.message = "There is no folder to download file from ftp"


class LostConfigError(Error):
    """There is no config file

        Args:
            message(str): Error message.

        Attributes:
            message(str): Error message.
    """

    def __init__(self, message):
        self.message = message
