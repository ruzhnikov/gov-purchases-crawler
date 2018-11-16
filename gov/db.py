# -*- coding: utf-8 -*-

# from sqlalchemy import create_engine, Column, Integer, String, DateTime
import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker, aliased, relationship
from sqlalchemy.ext.declarative import declarative_base
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
        arch = aliased(Archive, name="arch")
        query = sess.query(arch)

        archive = query.filter(arch.name_with_path == full_fname,
                               arch.name == fname,
                               arch.size == fsize).one_or_none()

        sess.close()

        return self._compare_fdata_and_return(archive, fsize)

    def _compare_fdata_and_return(self, db_file, fsize: int):
        """Проверить информацию по файлу из БД и вернуть результат.

        Args:
            db_file (Archive|ArchiveFile): Объект.
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
        archive = Archive(name=fname, name_with_path=full_fname, size=fsize)
        sess.add(archive)
        sess.commit()

        return archive.id

    def mark_archive_as_parsed(self, archive_id):
        sess = self.session()
        archive = sess.query(Archive).filter_by(id=archive_id).first()
        archive.has_parsed = True
        archive.parsed_on = dt.utcnow()
        sess.commit()

    def has_parsed_archive_file(self, archive_id: int, fname: str, fsize: int) -> bool:
        # TODO: подумать, что делать с файлом, который уже был распрасен и который изменился на сервере
        return False

    def get_archive_file_status(self, archive_id, fname, fsize):
        pass


# below we create DB models

_Base = declarative_base()


class Archive(_Base):
    __tablename__ = "archives"

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String, nullable=False)
    name_with_path = sa.Column(sa.String, nullable=False, unique=True)
    size = sa.Column(sa.Integer, nullable=False)
    downloaded_on = sa.Column(sa.DateTime, nullable=False, server_default=sa.text("NOW() AT TIME ZONE 'utc'"))
    parsed_on = sa.Column(sa.DateTime, nullable=True)
    updated_on = sa.Column(sa.DateTime, nullable=True)
    has_parsed = sa.Column(sa.Boolean, nullable=False, default=False)


class ArchiveFile(_Base):
    __tablename__ = "archive_files"

    id = sa.Column(sa.Integer, primary_key=True)
    archive_id = sa.Column(sa.Integer, sa.ForeignKey("archives.id"))
    name = sa.Column(sa.String, nullable=False)
    size = sa.Column(sa.Integer, nullable=False)
    parsed_on = sa.Column(sa.DateTime, nullable=True)
    has_parsed = sa.Column(sa.Boolean, nullable=False, default=False)

    archives = relationship("Archive")
