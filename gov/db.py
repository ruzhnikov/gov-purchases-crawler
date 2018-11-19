# -*- coding: utf-8 -*-

# from sqlalchemy import create_engine, Column, Integer, String, DateTime
import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker, aliased, relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime as dt
from .log import get_logger
from .errors import ItIsJustDBInterfaceError
from .config import DBConfig, AppConfig


class DBClient():
    """Интерфейс для работы с базой данных.
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
        self.archive = _Archive
        self.archive_file = _ArchiveFile
        self.ffl = _FourtyFourthLawContent

    def _connect(self):
        """Подключиться к БД
        """

        cfg = self._db_cfg
        conn_str = f"postgresql://{cfg.user}:{cfg.password}@{cfg.host}/{cfg.name}"
        engine_echo = True if self._app_cfg.mode == "dev" else False
        engine = sa.create_engine(conn_str, echo=engine_echo)
        self.session = sessionmaker(bind=engine)
        self._check_connection()

    def _check_connection(self):
        """Проверить коннект к базе
        """

        sess = self.session()
        sess.execute("SELECT TRUE")
        sess.close()

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
        arch = aliased(_Archive, name="arch")
        query = sess.query(arch)

        archive = query.filter(arch.name_with_path == full_fname,
                               arch.name == fname,
                               arch.size == fsize).one_or_none()

        sess.close()

        return self._compare_fdata_and_return(archive, fsize)

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
        archive = _Archive(name=fname, name_with_path=full_fname, size=fsize)
        sess.add(archive)
        sess.commit()

        return archive.id

    def mark_archive_as_parsed(self, archive_id):
        sess = self.session()
        archive = sess.query(_Archive).filter_by(id=archive_id).first()
        archive.has_parsed = True
        archive.parsed_on = dt.utcnow()
        sess.commit()

    def add_archive_file(self, archive_id: int, fname: str, fsize: int) -> int:
        self.log.info("Add info to database about a new file inside archive")
        sess = self.session()

        file = _ArchiveFile(archive_id=archive_id, name=fname, size=fsize)
        sess.add(file)
        sess.commit()

        return file.id

    def get_archive_file_status(self, archive_id: int, fname: str, fsize: int) -> int:
        self.log.debug(f"Check, is there parsed file {fname} or no")
        sess = self.session()
        query = sess.query(_ArchiveFile)
        file = query.filter(_ArchiveFile.name == fname,
                            _ArchiveFile.archive_id == archive_id,
                            _ArchiveFile.size == fsize).one_or_none()

        sess.close()
        return self._compare_fdata_and_return(file, fsize)

    def mark_archive_file_as_parsed(self, file_id, session=None):
        sess = session if session is not None else self.session()
        archive = sess.query(_ArchiveFile).filter_by(id=file_id).first()
        archive.has_parsed = True
        archive.parsed_on = dt.utcnow()
        if session is None:
            sess.commit()

    def add_ffl_content(self, file_id: int, content: dict):
        sess = self.session()
        content["archive_file_id"] = file_id
        ffl = _FourtyFourthLawContent(**content)
        sess.add(ffl)
        self.mark_archive_file_as_parsed(file_id, session=sess)

        sess.commit()

    def add(self, table_object, session=None):
        sess = session if session is not None else self.session()
        sess.add(table_object)

        if session is None:
            sess.commit()

# below we create DB models


_Base = declarative_base()


class _Archive(_Base):
    __tablename__ = "archives"

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String, nullable=False)
    name_with_path = sa.Column(sa.String, nullable=False, unique=True)
    size = sa.Column(sa.Integer, nullable=False)
    downloaded_on = sa.Column(sa.DateTime, nullable=False, server_default=sa.text("NOW() AT TIME ZONE 'utc'"))
    parsed_on = sa.Column(sa.DateTime, nullable=True)
    updated_on = sa.Column(sa.DateTime, nullable=True)
    has_parsed = sa.Column(sa.Boolean, nullable=False, default=False)


class _ArchiveFile(_Base):
    __tablename__ = "archive_files"

    id = sa.Column(sa.Integer, primary_key=True)
    archive_id = sa.Column(sa.Integer, sa.ForeignKey("archives.id"))
    name = sa.Column(sa.String, nullable=False)
    size = sa.Column(sa.Integer, nullable=False)
    parsed_on = sa.Column(sa.DateTime, nullable=True)
    has_parsed = sa.Column(sa.Boolean, nullable=False, default=False)

    archives = relationship("_Archive")


class _FourtyFourthLawContent(_Base):
    __tablename__ = "fourty_fourth_law_content"

    id = sa.Column(sa.Integer, primary_key=True)
    archive_file_id = sa.Column(sa.Integer, sa.ForeignKey("archive_files.id"))
    purchase_number = sa.Column(sa.String, nullable=True)
    href = sa.Column(sa.String, nullable=True)
    purchase_object_info = sa.Column(sa.String, nullable=True)
    placing_way = sa.Column(JSONB, nullable=True)
    etp = sa.Column(JSONB, nullable=True)
    purchase_responsible = sa.Column(JSONB, nullable=True)
    procedure_info = sa.Column(JSONB, nullable=True)
    lot = sa.Column(JSONB, nullable=True)

    archive_files = relationship("_ArchiveFile")
