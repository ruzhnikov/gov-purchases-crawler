
# -*- coding: utf-8 -*-


_REASON_CODES = {
    "FILE_EXISTS_BUT_NOT_PARSED": 1,
    "FILE_EXISTS_BUT_SIZE_DIFFERENT": 2
}
_REASONS = {
    _REASON_CODES["FILE_EXISTS_BUT_NOT_PARSED"]: "File was upload early, but not parsed yet",
    _REASON_CODES["FILE_EXISTS_BUT_SIZE_DIFFERENT"]: "File was upload and parsed early, but current size of file is different"
}


__all__ = []
