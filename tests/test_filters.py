
# -*- coding: utf-8 -*-

import pytest
from datetime import datetime as dt
from gov import filters


class TestEqual():
    def test_date(self):
        filter_str = """[{"field": "date", "match": "==", "value": "2019-02-01"}]"""
        date_from_filter = dt.strptime("2019-02-01", "%Y-%m-%d")
        date = dt.strptime("2019-02-01", "%Y-%m-%d")
        f = filters.parse_filter(filter_str)

        assert f.has_date_filter is True
        assert f.filter_date(date) is True
        assert filters._op_equal(date, date_from_filter) is True

    def test_region(self):
        filter_str = """[{"field": "region", "match": "==", "value": "Adygeja_Resp", "ignoreCase": true}]"""
        region = "Adygeja_Resp"

        f = filters.parse_filter(filter_str)

        assert f.has_region_filter is True
        assert f.filter_region(region) is True
        assert f.filter_region(region.lower()) is True
        assert filters._op_equal(region, region) is True
        assert filters._op_equal(region.lower(), region) is False
        assert filters._op_equal(region.lower(), region, True) is True
