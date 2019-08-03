
# -*- coding: utf-8 -*-

from enum import Enum


class ReasonCode(Enum):
    FILE_EXISTS_BUT_NOT_PARSED = 1
    FILE_EXISTS_BUT_SIZE_DIFFERENT = 2


class Reason(Enum):
    FILE_EXISTS_BUT_NOT_PARSED = "File was upload early, but not parsed yet"
    FILE_EXISTS_BUT_SIZE_DIFFERENT = "File was upload and parsed early, but current size of file is different"


def get_reason_by_code(code: ReasonCode) -> str:
    if code == ReasonCode.FILE_EXISTS_BUT_NOT_PARSED:
        return Reason.FILE_EXISTS_BUT_NOT_PARSED.value
    elif code == ReasonCode.FILE_EXISTS_BUT_SIZE_DIFFERENT:
        return Reason.FILE_EXISTS_BUT_SIZE_DIFFERENT.value
    else:
        return "Unknown reason"
