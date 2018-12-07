
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


def recursive_read_dict(element, skip_tags=(), tag_handlers={}):
    """Convert XML element to dict or text.

    Args:
        elem (etree.Element): Element of XML.
        skip_tags (tuple): List of tags that should be skipped.
        tag_handlers (dict): Handler for several tags.

    Returns:
        tuple: Tag and element structure in dict or text.
    """

    elements = list(element)
    tag = get_tag(element.tag)

    element_data = None

    if len(elements) == 0:
        if tag in tag_handlers.keys() and callable(tag_handlers[tag]):
            handler = tag_handlers[tag]
        else:
            handler = bool_replace
        element_data = handler(element.text) if element.text else None
    else:
        local_dict = {}
        for local_elem in elements:
            key, val = recursive_read_dict(local_elem, skip_tags, tag_handlers)
            if key in skip_tags:
                continue
            if key in local_dict.keys():
                if isinstance(local_dict[key], dict):
                    local_dict[key] = [ local_dict[key], val ]
                else:
                    local_dict[key].append(val)
                continue
            local_dict[key] = val

        element_data = local_dict

    return tag, element_data


def convert_date_to_utc(date_str):
    dt = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S%z")
    dt = dt.replace(tzinfo=timezone.utc) - dt.utcoffset()

    return dt.strftime("%Y-%m-%dT%H:%M:%S")


def remove_signature(elem_data: dict):
    if "signature" in elem_data:
        del elem_data["signature"]

    return elem_data
