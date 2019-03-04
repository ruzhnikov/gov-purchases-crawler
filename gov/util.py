
# -*- coding: utf-8 -*-

import re
from datetime import datetime as dt


_ARCHIVE_DT_PATTERN = re.compile(r"^\d+$")
_ARCHIVE_DT_TEMPLATE = "%Y%m%d%H"


def get_archive_date(archive_name: str):
    archive_date_str = None
    for archive_part in archive_name.split("_"):
        if _ARCHIVE_DT_PATTERN.match(archive_part):
            archive_date_str = archive_part
            break

    if archive_date_str is None:
        return None, f"Cannot find date part in the archive {archive_name}"

    try:
        archive_date = dt.strptime(archive_date_str, _ARCHIVE_DT_TEMPLATE)
    except ValueError as error:
        return None, error
    else:
        return archive_date, None
