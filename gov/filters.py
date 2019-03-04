
# -*- coding: utf-8 -*-

"""Module for reading and parsing obtained filters
"""


import json
import re
from datetime import datetime as dt
from .errors import UnknownFilterMatchError, WrongFilterFormatError, WrongFilterFieldError


def _op_like(a, b, ignore_case=False):
    pattern = r".*" + re.escape(a) + r".*"
    flags = re.IGNORECASE if ignore_case else 0
    return re.search(pattern, b, flags) is not None


def _op_not_like(a, b, ignore_case=False):
    return not _op_like(a, b, ignore_case)


def _op_begin(a, b, ignore_case=False):
    pattern = re.escape(b) + r".*"
    flags = re.IGNORECASE if ignore_case else 0
    return re.search(pattern, a, flags) is not None


def _op_end(a, b, ignore_case=False):
    pattern = r".*" + re.escape(b)
    flags = re.IGNORECASE if ignore_case else 0
    return re.search(pattern, a, flags) is not None


def _op_in(a, b: list, ignore_case=False):
    if not isinstance(b, list):
        raise TypeError(f"{b} must be list")

    if type(a) is str and ignore_case:
        a = str.lower(a)

    return a in b


def _op_not_in(a, b: list, ignore_case=False):
    return not _op_in(a, b, ignore_case)


def _op_between(a, b: list, ignore_case=False):
    if not isinstance(b, list):
        raise TypeError(f"{b} must be list")

    if len(b) != 2:
        raise ValueError(f"{b} must containt only 2 values")

    if type(a) is str and ignore_case:
        a = str.lower(a)

    return a >= b[0] and a <= b[1]


def _op_not_between(a, b: list, ignore_case=False):
    return not _op_between(a, b, ignore_case)


def _op_equal(a, b, ignore_case=False):
    if type(a) is str and type(b) is str and ignore_case:
        a = str.lower(a)
        b = str.lower(b)

    return a == b


def _op_not_equal(a, b, ignore_case=False):
    return not _op_equal(a, b, ignore_case)


def _op_more_or_equal(a, b, ignore_case=False):
    if type(a) is str and type(b) is str and ignore_case:
        a = str.lower(a)
        b = str.lower(b)

    return a >= b


def _op_more(a, b, ignore_case=False):
    if type(a) is str and type(b) is str and ignore_case:
        a = str.lower(a)
        b = str.lower(b)

    return a > b


def _op_less_or_equal(a, b, ignore_case=False):
    if type(a) is str and type(b) is str and ignore_case:
        a = str.lower(a)
        b = str.lower(b)

    return a <= b


def _op_less(a, b, ignore_case=False):
    if type(a) is str and type(b) is str and ignore_case:
        a = str.lower(a)
        b = str.lower(b)

    return a < b


_AVAIL_FIELDS = ("date", "region")

_OPERATORS = {
    "==": _op_equal,
    "!=": _op_not_equal,
    ">=": _op_more_or_equal,
    "<=": _op_less_or_equal,
    ">": _op_more,
    "<": _op_less,
    "like": _op_like,
    "not like": _op_not_like,
    "between": _op_between,
    "not between": _op_not_between,
    "in": _op_in,
    "not in": _op_not_in,
    "begin": _op_begin,
    "end": _op_end
}

_OPERATORS["="] = _OPERATORS["eq"] = _OPERATORS["=="]
_COMPLEX_MATCHES = ("in", "not in", "between", "not between")
_LIKE_MATCHES = ("like", "not like", "begin", "end")
_NEGATIVE_MATCHES = frozenset(("!=", "not like", "not between", "not in"))
_POSITIVE_MATCHES = set(_OPERATORS.keys()) ^ _NEGATIVE_MATCHES
_DEFAULT_MATCH = "=="
_FILTERS = {}
_MANDATORY_FILTER_FIELDS = frozenset(("field", "value"))


def _read_filter(filter_dict: dict):
    filter_keys = set(filter_dict.keys())
    if not filter_keys.issuperset(_MANDATORY_FILTER_FIELDS):
        raise WrongFilterFormatError(f"""Wrong format of filter {str(filter_dict)}.
        Please, use format
        {{"field": "<field>", "match": "<match>", "value": "<value>", "ignorecase": <true|false>}}
        OR
        {{"field": "<field>", "value": "<value>", "ignorecase": <true|false>}}""")

    filter_field = str.lower(filter_dict["field"])
    _check_field(filter_field)
    filter_match = filter_dict.get("match")
    if filter_match is None:
        filter_match = _DEFAULT_MATCH
    filter_match = str.lower(filter_match)
    _check_match(filter_match, filter_field)

    # ignorecase
    filter_ignore_case = filter_dict.get("ignorecase") or filter_dict.get(
        "ignore_case") or filter_dict.get("ignoreCase")
    if filter_ignore_case is None:
        filter_ignore_case = False
    elif type(filter_ignore_case) is not bool:
        filter_ignore_case = False

    # filter value
    filter_value = filter_dict["value"]
    if filter_field == "date":
        filter_value = _prepare_date_value(filter_value, filter_match)
    elif filter_field == "region":
        filter_value = _prepare_region_value(filter_value, filter_match, filter_ignore_case)

    _FILTERS[filter_field] = {
        "match": filter_match,
        "value": filter_value,
        "ignore_case": filter_ignore_case
    }


def _check_field(field: str):
    if field not in _AVAIL_FIELDS:
        raise WrongFilterFieldError(f"Unknown field {field}; Available fields are {str(_AVAIL_FIELDS)}")


def _check_match(match: str, field: str):
    if match not in _OPERATORS:
        raise UnknownFilterMatchError(f"Unknown match {match}")

    if field == "date" and match in _LIKE_MATCHES:
        raise WrongFilterFieldError(f"The 'date' field does not support match {match}")


def _prepare_date_value(date: str, match_str: str):
    def split_date(date_str):
        # simple checker of date format. If there is 2 parts separated by space,
        # we have datetime in format "%Y-%m-%d %H:%M:%S"
        # If there is one part, we have only date in format "%Y-%m-%d" and should add time self
        splitted_date = date_str.split()
        if len(splitted_date) == 2:
            return dt.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        elif len(splitted_date) == 1:
            return dt.strptime(date_str, "%Y-%m-%d")
        else:
            raise ValueError("The date has to be in either '%Y-%m-%d %H:%M:%S' or '%Y-%m-%d' format")

    if match_str in _COMPLEX_MATCHES:
        returned_date = []
        for part_date in date:
            returned_date.append(split_date(part_date))
    else:
        returned_date = split_date(date)

    return returned_date


def _prepare_region_value(region, match_str: str, ignore_case: bool):
    if not ignore_case:
        return region

    if match_str in (_COMPLEX_MATCHES, _LIKE_MATCHES):
        return [str.lower(local_region) for local_region in region]
    else:
        return str.lower(region)


def parse_filter(filter_str):
    """Read and parse filters from filter_str

    Args:
        filter_str (str): String with filters. Filters has to be in JSON and has format such as

    `[{"field": "date", "match": "==", "value": "2019-01-12 00:10:00"}]`
    OR
    `{"field": "date", "match": "==", "value": "2019-01-12 00:10:00"}`

    Returns:
        filter._Filters: Filters object.
    """
    parsed_filter = json.loads(filter_str)
    if isinstance(parsed_filter, dict):
        _read_filter(parsed_filter)
    else:
        for local_filter in parsed_filter:
            _read_filter(local_filter)

    filters = _Filters(_FILTERS)
    return filters


def get_help():
    """Return help message about filter"""

    # TODO: finish the function
    return "Parser filters"


class _Filters():
    def __init__(self, prepared_filters: dict):
        self._date_filter = prepared_filters.get("date")
        self._region_filter = prepared_filters.get("region")

    @property
    def has_date_filter(self):
        return self._date_filter is not None

    @property
    def has_region_filter(self):
        return self._region_filter is not None

    @property
    def is_positive_date_match(self):
        return self.has_date_filter and self._date_filter["match"] in _POSITIVE_MATCHES

    @property
    def is_positive_region_match(self):
        return self.has_region_filter and self._region_filter["match"] in _POSITIVE_MATCHES

    def filter_date(self, date: dt) -> bool:
        if not self.has_date_filter:
            return False

        if not isinstance(date, dt):
            raise TypeError(f"{date} must be instance of datetime.datetime")

        return self._invoke_filter(date, self._date_filter)

    def filter_region(self, region: str) -> bool:
        if not self.has_region_filter:
            return False

        return self._invoke_filter(region, self._region_filter)

    def _invoke_filter(self, filtered_value, filter_dict):
        op_func = _OPERATORS[filter_dict["match"]]
        ignore_case = filter_dict["ignore_case"]
        value = filter_dict["value"]

        return op_func(filtered_value, value, ignore_case)
