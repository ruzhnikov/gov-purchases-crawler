
# -*- coding: utf-8 -*-

from lxml import etree


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
        if tag in tag_handlers and callable(tag_handlers[tag]):
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

            # We can have two or more subelements with the same name.
            # Combine these elements into array
            if key in local_dict:
                if isinstance(local_dict[key], dict):
                    local_dict[key] = [local_dict[key], val]
                else:
                    local_dict[key].append(val)
                continue
            local_dict[key] = val

        element_data = local_dict

    return tag, element_data


def get_xml_data(raw_xml: bytes, skip_tags=(), tag_handlers={}):
    """Read XML data, convert it to needle format and return these data.

    Args:
        raw_xml (bytes): Raw XML data in bytes.
        skip_tags (tuple, optional): Tags of XML that should be skipped. Defaults to ().
        tag_handlers (dict, optional): Special handlers for XML tags. Defaults to {}.

    Returns:
        tuple(str, dict): Name of root XML element and parsed XML data as dictionary.
    """
    root = etree.fromstring(raw_xml)
    root_element = list(root)[0]
    xml_type = get_tag(root_element)

    _, file_data = recursive_read_dict(root, skip_tags, tag_handlers)

    return xml_type, file_data
