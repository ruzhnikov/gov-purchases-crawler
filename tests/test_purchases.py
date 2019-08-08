
# -*- coding: utf-8 -*-

import pytest
import logging
from gov.purchases_new import Client


def test_create_client(monkeypatch):
    def mock_connect(self):
        self._is_connected = True

    monkeypatch.setattr(Client, "_connect", mock_connect)
    client = Client("1.1.1.1", logging.getLogger(), "protocols")

    assert client is not None
    assert client._is_connected is True
    assert client._server_folder == "protocols"


def test_set_region_skipped(monkeypatch):
    def mock_connect(self):
        self._is_connected = True

    monkeypatch.setattr(Client, "_connect", mock_connect)
    client = Client("1.1.1.1", logging.getLogger())

    assert client is not None
    assert client._skipped_region is None

    client.set_region_skipped("Region")
    assert client._skipped_region == "Region"


def test_regions(monkeypatch):
    def mock_connect(self):
        self._is_connected = True

    monkeypatch.setattr(Client, "_connect", mock_connect)
    client = Client("1.1.1.1", logging.getLogger())

    assert client is not None
    assert client.regions == []
