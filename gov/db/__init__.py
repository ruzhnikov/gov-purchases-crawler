
# -*- coding: utf-8 -*-

"""A wrapper over database.
"""

import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker, aliased, relationship
from datetime import datetime as dt
from ..log import get_logger
from ..config import DBConfig, AppConfig
from . import models


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
        self._app_cfg = AppConfig()
        self._db_cfg = DBConfig()
        self._connect()

    def _connect(self):
        cfg = self._db_cfg
        conn_str = f"postgresql://{cfg.user}:{cfg.password}@{cfg.host}/{cfg.name}"
        engine_echo = True if self._app_cfg.mode == "dev" else False
        if self._db_cfg.echo is not None:
            engine_echo = self._db_cfg.echo == "yes"

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

    def get_archive_status(self, full_fname: str, fname: str, fsize: int):
        """Проверяет, есть ли в БД уже распарсенный файл или нет.

        Args:
            full_fname (str): Файл с полным путём до него на сервере.
            fname (str): Имя файла.
            fsize (int): Размер файла.

        Returns:
            bool: Результат проверки.
        """

        self.log.debug(f"Check, is there parsed file {fname} or no")
        sess = self.session()
        arch = aliased(models.Archive, name="arch")
        query = sess.query(arch)

        archive = query.filter(arch.name_with_path == full_fname,
                               arch.name == fname,
                               arch.size == fsize).one_or_none()

        sess.close()

        return self._compare_fdata_and_return(archive, fsize)

    def add_archive(self, full_fname: str, fname: str, fsize: int) -> int:
        """Добавляет информацию об архиве в БД. Возвращает ID новой записи.

        Args:
            full_fname (str): Файл с полным путём до него на сервере.
            fname (str): Имя файла.
            fsize (int): Размер файла.

        Returns:
            int: ID новой записи.
        """

        self.log.info("Add info about a new archive to database")
        sess = self.session()
        archive = models.Archive(name=fname, name_with_path=full_fname, size=fsize)
        sess.add(archive)
        sess.commit()

        return archive.id

    def mark_archive_as_parsed(self, archive_id):
        sess = self.session()
        archive = sess.query(models.Archive).filter_by(id=archive_id).first()
        archive.has_parsed = True
        archive.parsed_on = dt.utcnow()
        sess.commit()

    def add_archive_file(self, archive_id: int, fname: str, fsize: int) -> int:
        self.log.info("Add info to database about a new file inside archive")
        sess = self.session()

        file = models.ArchiveFile(archive_id=archive_id, name=fname, size=fsize)
        sess.add(file)
        sess.commit()

        return file.id

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

    def mark_archive_file_as_parsed(self, file_id, xml_type, session=None, reason=None):
        sess = session if session is not None else self.session()
        file = sess.query(models.ArchiveFile).filter_by(id=file_id).first()
        file.has_parsed = True
        file.parsed_on = dt.utcnow()
        file.reason = reason
        file.xml_type = xml_type
        if session is None:
            sess.commit()

    def update_archive_file(self, file_id: int, session=None, **content):
        pass


class FortyFourthLawDB(DBClient):
    def __init__(self):
        super().__init__()
        self.often_tags_table = models.FFLNotificationOftenTags
        self.rare_tags_table = models.FFLNotificationRareTags
        self.unknown_tags_table = models.FFLNotificationUnknownTags

    def get_columns_dict(self, table) -> list:
        columns = sa.inspect(table).columns

        sess = self.session()
        for row in sess.query(models.FFLTagsToFieldsDict).all():
            if columns.has_key(row.field):
                yield row.tag, row.field

        sess.close()