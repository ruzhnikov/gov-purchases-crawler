
# -*- coding: utf-8 -*-

import pytest
from lxml import etree
from gov.law import util


simple_xml = b"""<?xml version="1.0" encoding="UTF-8"?>
<export xmlns="http://localhost/oos/export/1" xmlns:oos="http://localhost/oos/types/1" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <fcsContractSign schemeVersion="1.0">
        <oos:id>4780921</oos:id>
    </fcsContractSign>
</export>
"""


def test_get_tag():
    root = etree.fromstring(simple_xml)
    root_element = list(root)[0]
    tag_id = list(root_element)[0]

    assert util.get_tag(root_element) == "fcsContractSign"
    assert util.get_tag(tag_id) == "id"


def test_bool_replace():
    true_txt = "true"
    false_txt = "false"
    other_txt = "Just other text"

    assert util.bool_replace(true_txt) == True
    assert util.bool_replace(false_txt) == False
    assert util.bool_replace(other_txt) == other_txt
