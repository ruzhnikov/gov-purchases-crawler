
# -*- coding: utf-8 -*-

from lxml import etree


def get_tag(tag):
    """Возвращает tag, очищенный от неймспейса"""

    return etree.QName(tag).localname
