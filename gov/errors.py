
# -*- coding: utf-8 -*-


class Error(Exception):
    """Base class for exceptions in this module."""
    pass


class WrongReaderLawError(Error):
    """A wrong law number has been got.

    Args:
        law (int): Law number.

    Attributes:
        message (str): Error message.
        law (int): Law number.
    """

    def __init__(self, law):
        self.message = "Wrong law {}".format(law)
        self.law = law


class EmptyDownloadDirError(Error):
    """There is no a folder for downloading files.
    The folder was not be set during create an object and wasn't obtained in a method call.

    Attributes:
        message (str): Error message.
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


class UnknownFilterMatchError(Error):
    def __init__(self, message):
        self.message = message


class WrongFilterFormatError(Error):
    def __init__(self, message):
        self.message = message


class WrongFilterFieldError(Error):
    def __init__(self, message):
        self.message = message


class EmptyValue(Error):
    def __init__(self, message):
        self.message = message
