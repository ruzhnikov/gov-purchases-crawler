
# -*- coding: utf-8 -*-

"""A wrapper over database.
"""

import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker, aliased, relationship
from datetime import datetime as dt
from ..log import get_logger
from ..config import conf, is_production
from . import models
from . import _fourty_forth_law_model as ffl_model


class DBClient():
    """Interface to work with database.
    """

    FILE_STATUS = {
        "FILE_EXISTS": 1,
        "FILE_DOES_NOT_EXIST": 2,
        "FILE_EXISTS_BUT_NOT_PARSED": 3,
        "FILE_EXISTS_BUT_SIZE_DIFFERENT": 4
    }

    def __init__(self):
        self.log = get_logger(__name__)
        self._connect()

    def _connect(self):
        cfg = conf("db")
        conn_str = f"postgresql://{cfg['user']}:{cfg['password']}@{cfg['host']}:{cfg['port']}/{cfg['name']}"
        engine_echo = not is_production()
        if cfg["echo"] is not None:
            engine_echo = cfg["echo"] == True

        engine = sa.create_engine(conn_str, echo=engine_echo)
        self.session = sessionmaker(bind=engine)
        self._check_connection()

    def _check_connection(self):
        sess = self.session()
        sess.execute("SELECT TRUE")
        sess.close()

    def _compare_fdata_and_return(self, db_file, fsize: int):
        """Проверить информацию по файлу из БД и вернуть результат.

        Args:
            db_file (_Archive|_ArchiveFile): Объект.
            fsize (int): Размер файла с FTP сервера.

        Returns:
            int: Одно из значений self.FILE_STATUS
        """
        if db_file is None:
            return self.FILE_STATUS["FILE_DOES_NOT_EXIST"]
        elif db_file.size != fsize:
            return self.FILE_STATUS["FILE_EXISTS_BUT_SIZE_DIFFERENT"]
        elif db_file.has_parsed == False:
            return self.FILE_STATUS["FILE_EXISTS_BUT_NOT_PARSED"]
        else:
            return self.FILE_STATUS["FILE_EXISTS"]

    def get_archive_status(self, fname: str, fsize: int):
        """Проверяет, есть ли в БД уже распарсенный файл или нет.

        Args:
            fname (str): Имя файла.
            fsize (int): Размер файла.

        Returns:
            bool: Результат проверки.
        """

        self.log.debug(f"Check, is there parsed file {fname} or no")
        sess = self.session()
        arch = aliased(models.Archive, name="arch")
        query = sess.query(arch)

        archive = query.filter(arch.name == fname,
                               arch.size == fsize).one_or_none()

        sess.close()

        return self._compare_fdata_and_return(archive, fsize)

    def get_archive(self, fname: str, fsize: int) -> models.Archive:
        sess = self.session()
        query = sess.query(models.Archive)

        archive = query.filter(models.Archive.name == fname,
                               models.Archive.size == fsize).first()
        sess.close()

        return archive

    def add_archive(self, fname: str, fsize: int, law_number: str, folder_name: str) -> int:
        """Add information about archive to DB. Return ID of new record.

        Args:
            fname (str): File name.
            fsize (int): File size.
            law_number (str): Law number
            folder_name (str): Folder name.

        Returns:
            int: [description]
        """

        self.log.debug(f"Add info about a new archive {fname} to database")
        sess = self.session()
        archive = models.Archive(name=fname, size=fsize, law_number=law_number, folder_name=folder_name)
        sess.add(archive)
        sess.commit()

        archive_id = archive.id
        sess.close()

        return archive_id

    def mark_archive_as_parsed(self, archive_id):
        sess = self.session()
        archive = sess.query(models.Archive).filter_by(id=archive_id).first()
        archive.has_parsed = True
        archive.parsed_on = dt.utcnow()
        sess.commit()
        sess.close()

    def add_archive_file(self, archive_id: int, fname: str, fsize: int) -> int:
        self.log.debug(f"Add info to database about a new file {fname} inside archive")
        sess = self.session()

        file = models.ArchiveFile(archive_id=archive_id, name=fname, size=fsize)
        sess.add(file)
        sess.commit()

        file_id = file.id
        sess.close()

        return file_id

    def get_archive_file_status(self, archive_id: int, fname: str, fsize: int) -> int:
        self.log.debug(f"Check, is there parsed file {fname} or no")
        sess = self.session()
        arch_file = aliased(models.ArchiveFile, name="arch_file")
        query = sess.query(arch_file)
        file = query.filter(arch_file.name == fname,
                            arch_file.archive_id == archive_id,
                            arch_file.size == fsize).one_or_none()

        sess.close()
        return self._compare_fdata_and_return(file, fsize)

    def get_archive_file(self, archive_id: int, fname: str, fsize: int) -> models.ArchiveFile:
        sess = self.session()
        arch_file = aliased(models.ArchiveFile, name="arch_file")
        query = sess.query(arch_file)
        file = query.filter(arch_file.name == fname,
                            arch_file.archive_id == archive_id,
                            arch_file.size == fsize).first()

        sess.close()
        return file

    def mark_archive_file_as_parsed(self, file_id, xml_type, session=None, reason=None):
        sess = session if session is not None else self.session()
        file = sess.query(models.ArchiveFile).filter_by(id=file_id).first()
        file.has_parsed = True
        file.parsed_on = dt.utcnow()
        file.reason = reason
        file.xml_type = xml_type
        if session is None:
            sess.commit()
            sess.close()

    def delete_archive_files(self, archive_id: int):
        sess = self.session()
        sess.query(models.ArchiveFile).filter(models.ArchiveFile.archive_id == archive_id).delete()
        sess.commit()
        sess.close()


class FortyFourthLawDB(DBClient):
    """Class for working with DB of 44th law
    """

    class _Notifications():
        """Wrapper around notification_* tables"""

        def __init__(self):
            self.often_tags_table = ffl_model.FFLNotificationOftenTags
            self.rare_tags_table = ffl_model.FFLNotificationRareTags
            self.unknown_tags_table = ffl_model.FFLNotificationsUnknownTags

    class _Protocols():
        """Wrapper around protocols_* tables"""

        def __init__(self):
            self.often_tags_table = ffl_model.FFLProtocolsOftenTags
            self.rare_tags_table = ffl_model.FFLProtocolRareTags
            self.unknown_tags_table = ffl_model.FFLProtocolsUnknownTags

    def __init__(self):
        super().__init__()
        self.protocols = self._Protocols()
        self.notifications = self._Notifications()

    def get_columns_dict(self, table) -> list:
        columns = sa.inspect(table).columns

        sess = self.session()
        for row in sess.query(ffl_model.FFLTagsToFieldsDict).all():
            if columns.has_key(row.field):
                yield row.tag, row.field

        sess.close()

    def delete_file_tags(self, file_id: int):
        """Delete all rows related with file_id from all forty_fourth_law.* tables

        Args:
            file_id (int): ID of XML file.
        """
        sess = self.session()
        for model in (self.notifications, self.protocols):
            for table in (model.often_tags_table, model.rare_tags_table, model.unknown_tags_table):
                sess.query(table).filter(table.archive_file_id == file_id).delete()
        sess.commit()
        sess.close()
