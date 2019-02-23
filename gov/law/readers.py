
# -*- coding: utf-8 -*-

"""A module for working with purchases over different laws.
"""


from . import _ffl_readers


class FFLReaders():
    """Entry point for readers"""

    def __init__(self, killer):
        self.notifications = _ffl_readers.FortyFourthLawNotifications()
        self.notifications.set_killer(killer)
        self.protocols = _ffl_readers.FortyFourthLawProtocols()
        self.protocols.set_killer(killer)
