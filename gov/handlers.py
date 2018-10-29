
# -*- coding: utf-8 -*-

from .log import get_logger
from .utils import get_tag


log = get_logger(__name__)


def purchase_number(elem, return_in_dict=False):
    log.info("Handle {}".format(get_tag(elem.tag)))
    for e in elem.iter():
        log.info("{} => {}".format(get_tag(e.tag), e.text))


def placing_way(elem):
    log.info("Handle {}".format(get_tag(elem.tag)))
    for e in elem.iter():
        log.info("{} => {}".format(get_tag(e.tag), e.text))


def purchase_responsible(elem):
    log.info("Handle {}".format(get_tag(elem.tag)))
    for e in elem.iter():
        log.info("{} => {}".format(get_tag(e.tag), e.text))


def etp(elem):
    log.info("Handle {}".format(get_tag(elem.tag)))
    for e in elem.iter():
        log.info("{} => {}".format(get_tag(e.tag), e.text))


def procedure_info(elem):
    log.info("Handle {}".format(get_tag(elem.tag)))
    for e in elem.iter():
        log.info("{} => {}".format(get_tag(e.tag), e.text))


def lot(elem):
    log.info("Handle {}".format(get_tag(elem.tag)))
    for e in elem.iter():
        log.info("{} => {}".format(get_tag(e.tag), e.text))
