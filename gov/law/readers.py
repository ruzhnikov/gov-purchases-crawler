
# -*- coding: utf-8 -*-

"""A module for working with purchases over different laws.
"""


from . import _ffl_readers


class FFLReaders():
    """Entry point for readers"""

    def __init__(self):
        self.notifications = _ffl_readers.FortyFourthLawNotifications()
        self.protocols = _ffl_readers.FortyFourthLawProtocols()
