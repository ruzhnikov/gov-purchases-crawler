
# -*- coding: utf-8 -*-

from lxml import etree
from datetime import datetime
from datetime import timezone


def get_tag(tag):
    """Read, clean from namespaces and return a tag of XML element.

    Args:
        tag (str): Tag.

    Returns:
        str: Tag without namespaces.
    """
    return etree.QName(tag).localname


def bool_replace(text):
    """In text replace str values 'true' and 'false' by boolean values

    Args:
        text (str): Incoming text.

    Returns:
        str: Formatted text.
    """
    if text == "false":
        return False
    elif text == "true":
        return True
    else:
        return text


def recursive_dict(elem):
    """Convert XML element to dict or text.
    Taken by link https://lxml.de/FAQ.html#how-can-i-map-an-xml-tree-into-a-dict-of-dicts

    Args:
        elem (etree.Element): Element of XML.

    Returns:
        tuple: Tag and element structure in dict or text.
    """
    return get_tag(elem.tag), dict(map(recursive_dict, elem)) or bool_replace(elem.text)


def convert_date_to_utc(date_str):
    dt = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S%z")
    dt = dt.replace(tzinfo=timezone.utc) - dt.utcoffset()

    return dt.strftime("%Y-%m-%dT%H:%M:%S")


def remove_signature(elem_data: dict):
    if "signature" in elem_data:
        del elem_data["signature"]

    return elem_data
