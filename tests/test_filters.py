
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
        assert f.is_positive_region_match is True
        assert filters._op_equal(region, region) is True
        assert filters._op_equal(region.lower(), region) is False
        assert filters._op_equal(region.lower(), region, True) is True


class TestNotEqual():
    def test_date(self):
        filter_str = """[{"field": "date", "match": "!=", "value": "2019-02-01"}]"""
        date_from_filter = dt.strptime("2019-02-01", "%Y-%m-%d")
        date_equal = dt.strptime("2019-02-01", "%Y-%m-%d")
        date_not_equal_less = dt.strptime("2019-01-31", "%Y-%m-%d")
        date_not_equal_more = dt.strptime("2019-02-10", "%Y-%m-%d")

        f = filters.parse_filter(filter_str)
        assert f.has_date_filter is True
        assert f.filter_date(date_equal) is False
        assert f.filter_date(date_not_equal_less) is True
        assert f.filter_date(date_not_equal_more) is True
        assert f.is_positive_date_match is False
        assert filters._op_not_equal(date_equal, date_from_filter) is False
        assert filters._op_not_equal(date_not_equal_less, date_from_filter) is True
        assert filters._op_not_equal(date_not_equal_more, date_from_filter) is True

    def test_region(self):
        pass


class TestMoreOrEqual():
    def test_date(self):
        filter_str = """[{"field":"date","match":">=","value":"2019-01-01"}]"""
        date_from_filter = dt.strptime("2019-01-01", "%Y-%m-%d")
        date_equal = dt.strptime("2019-01-01", "%Y-%m-%d")
        date_more = dt.strptime("2019-01-02", "%Y-%m-%d")
        date_less = dt.strptime("2018-12-31", "%Y-%m-%d")

        f = filters.parse_filter(filter_str)
        assert f.has_date_filter is True
        assert f.filter_date(date_equal) is True
        assert f.filter_date(date_more) is True
        assert f.filter_date(date_less) is False
        assert f.is_positive_date_match is True

        assert filters._op_more_or_equal(date_equal, date_from_filter) is True
        assert filters._op_more_or_equal(date_more, date_from_filter) is True
        assert filters._op_more_or_equal(date_less, date_from_filter) is False
