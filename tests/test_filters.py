
# -*- coding: utf-8 -*-

import pytest
import json
from datetime import datetime as dt
from gov import filters
from gov import errors


class TestParseFilter():
    def test_wrong_filter_str(self):
        wrong_filter_str = "{]"
        with pytest.raises(json.decoder.JSONDecodeError):
            filters.parse_filter(wrong_filter_str)

        wrong_json_str = """{"field": "date", "match": "==", "value":}"""
        with pytest.raises(json.decoder.JSONDecodeError):
            filters.parse_filter(wrong_json_str)

    def test_wrong_field(self):
        wrong_json_str = """[{"field": "unknown field", "match": "==", "value": "2019-02-01"}]"""
        with pytest.raises(errors.WrongFilterFieldError):
            filters.parse_filter(wrong_json_str)

    def test_wrong_match(self):
        wrong_json_str = """[{"field": "region", "match": "=~", "value": "Moscow"}]"""
        with pytest.raises(errors.UnknownFilterMatchError):
            filters.parse_filter(wrong_json_str)

        wrong_json_str = """[{"field": "date", "match": "like", "value": "2019-02-01"}]"""
        with pytest.raises(errors.WrongFilterFieldError) as excinfo:
            filters.parse_filter(wrong_json_str)

        assert "'date' field does not support match" in str(excinfo.value)

    def test_wrong_date_format(self):
        filter_str = """[{"field": "date", "value": "2019-02-01 10:00:00 +300"}]"""
        with pytest.raises(ValueError) as excinfo:
            filters.parse_filter(filter_str)

        assert "date has to be in either" in str(excinfo.value)

    def test_default_match(self):
        filter_str = """[{"field": "date", "value": "2019-02-01"}]"""
        f = filters.parse_filter(filter_str)
        assert f.has_date_filter is True
        assert f.is_positive_date_match is True
        assert filters._FILTERS["date"]["match"] == filters._DEFAULT_MATCH


class TestEqual():
    def test_date(self):
        filter_str = """[{"field": "date", "match": "==", "value": "2019-02-01"}]"""
        date_from_filter = dt.strptime("2019-02-01", "%Y-%m-%d")
        date = dt.strptime("2019-02-01", "%Y-%m-%d")
        f = filters.parse_filter(filter_str)

        assert f.has_date_filter is True
        assert f.filter_date(date) is True
        assert f.is_positive_date_match is True
        assert f.is_negative_date_match is False
        assert filters._op_equal(date, date_from_filter) is True

    def test_region(self):
        filter_str = """[{"field": "region", "match": "==", "value": "Adygeja_Resp", "ignoreCase": true}]"""
        region = "Adygeja_Resp"

        f = filters.parse_filter(filter_str)

        assert f.has_region_filter is True
        assert f.filter_region(region) is True
        assert f.filter_region(region.lower()) is True
        assert f.is_positive_region_match is True
        assert f.is_negative_region_match is False
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
        assert f.is_negative_date_match is True
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
        assert f.is_negative_date_match is False

        assert filters._op_more_or_equal(date_equal, date_from_filter) is True
        assert filters._op_more_or_equal(date_more, date_from_filter) is True
        assert filters._op_more_or_equal(date_less, date_from_filter) is False


class TestLike():
    def test_region_with_case(self):
        filter_str = """[{"field": "region", "match": "like", "value": "Adygeja"}]"""

        f = filters.parse_filter(filter_str)
        assert f.has_region_filter is True
        assert f.is_positive_region_match is True
        assert filters._FILTERS["region"]["ignore_case"] is False
        assert f.filter_region("Adygeja_Resp") is True
        assert f.filter_region("Moskva") is False
        assert filters._op_like("Adygeja_Resp", "Adygeja") is f.filter_region("Adygeja_Resp")

    def test_region_without_case(self):
        filter_str = """{"field": "region", "match": "like", "value": "adygeja", "ignoreCase": true}"""

        f = filters.parse_filter(filter_str)
        assert f.has_region_filter is True
        assert f.is_positive_region_match is True
        assert filters._FILTERS["region"]["ignore_case"] is True

        assert f.filter_region("Adygeja_Resp") is True
        assert f.filter_region("Moskva") is False
        assert filters._op_like("Adygeja_Resp", "adygeja", ignore_case=True) is f.filter_region("Adygeja_Resp")

    def test_not_region_with_case(self):
        filter_str = """[{"field": "region", "match": "not like", "value": "Adygeja"}]"""

        f = filters.parse_filter(filter_str)
        assert f.has_region_filter is True
        assert f.is_negative_region_match is True
        assert filters._FILTERS["region"]["ignore_case"] is False
        assert f.filter_region("Adygeja_Resp") is False
        assert f.filter_region("adygeja_resp") is True
        assert f.filter_region("Moskv") is True

    def test_not_region_without_case(self):
        filter_str = """[{"field": "region", "match": "not like", "value": "adygeja", "ignoreCase": true}]"""

        f = filters.parse_filter(filter_str)
        assert f.has_region_filter is True
        assert f.is_negative_region_match is True
        assert filters._FILTERS["region"]["ignore_case"] is True
        assert f.filter_region("Adygeja_Resp") is False
        assert f.filter_region("adygeja_resp") is False
        assert f.filter_region("Moskv") is True


class TestBegin():
    def test_region_with_case(self):
        filter_str = """[{"field": "region", "match": "begin", "value": "Adygeja"}]"""

        f = filters.parse_filter(filter_str)
        assert f.has_region_filter is True
        assert f.is_positive_region_match is True
        assert filters._FILTERS["region"]["ignore_case"] is False
        assert f.filter_region("Adygeja_Resp") is True
        assert f.filter_region("Moskva") is False

    def test_region_without_case(self):
        filter_str = """{"field": "region", "match": "begin", "value": "adygeja", "ignoreCase": true}"""

        f = filters.parse_filter(filter_str)
        assert f.has_region_filter is True
        assert f.is_positive_region_match is True
        assert filters._FILTERS["region"]["ignore_case"] is True
        assert f.filter_region("Adygeja_Resp") is True
        assert f.filter_region("Moskva") is False


class TestEnd():
    def test_region_with_case(self):
        filter_str = """[{"field": "region", "match": "end", "value": "Resp"}]"""

        f = filters.parse_filter(filter_str)
        assert f.has_region_filter is True
        assert f.is_positive_region_match is True
        assert filters._FILTERS["region"]["ignore_case"] is False
        assert f.filter_region("Adygeja_Resp") is True
        assert f.filter_region("Moskva") is False

    def test_region_without_case(self):
        filter_str = """{"field": "region", "match": "end", "value": "resp", "ignoreCase": true}"""

        f = filters.parse_filter(filter_str)
        assert f.has_region_filter is True
        assert f.is_positive_region_match is True
        assert filters._FILTERS["region"]["ignore_case"] is True
        assert f.filter_region("Adygeja_Resp") is True
        assert f.filter_region("Moskva") is False
