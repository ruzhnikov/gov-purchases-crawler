
# -*- coding: utf-8 -*-

"""A wrapper over database.
"""

from enum import Enum
import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker, aliased
from datetime import datetime as dt
from .models import Archive, ArchiveFile
from ..log import get_logger
from ..config import conf, is_production


class FileStatus(Enum):
    """Statuses of file from DB.
    """

    FILE_EXISTS = 1
    FILE_DOES_NOT_EXIST = 2
    FILE_EXISTS_BUT_NOT_PARSED = 3
    FILE_EXISTS_BUT_SIZE_DIFFERENT = 4


class DBClient():
    """A base class for working with database.
        Other classes for working with data of difference laws, inherits from this one.
        The class contains methods for manipulate archive and archive's file information.
    """

    def __init__(self):
        self.log = get_logger(__name__)
        self._connect()

    def _connect(self):
        conn_str = self._get_connection_string()
        engine_echo = self._get_engine_echo()
        engine = sa.create_engine(conn_str, echo=engine_echo)

        self._session = sessionmaker(bind=engine)
        self._check_connection()

    def _get_connection_string(self):
        cfg = conf("db")
        conn_str = f"postgresql://{cfg['user']}:{cfg['password']}@{cfg['host']}:{cfg['port']}/{cfg['name']}"

        return conn_str

    def _get_engine_echo(self):
        cfg = conf("db")
        engine_echo = not is_production()
        if cfg["echo"] is not None:
            engine_echo = cfg["echo"] == True

        return engine_echo

    def _check_connection(self):
        sess = self._session()
        sess.execute("SELECT TRUE")
        sess.close()

    def _compare_fdata_and_return(self, db_file, fsize: int) -> FileStatus:
        """Check information about file(or archive) in DB and return result.

        Args:
            db_file (_Archive|_ArchiveFile): File.
            fsize (int): File size from server.

        Returns:
            FileStatus
        """
        if db_file is None:
            return FileStatus.FILE_DOES_NOT_EXIST
        elif db_file.size != fsize:
            return FileStatus.FILE_EXISTS_BUT_SIZE_DIFFERENT
        elif db_file.has_parsed == False:
            return FileStatus.FILE_EXISTS_BUT_NOT_PARSED
        else:
            return FileStatus.FILE_EXISTS

    def get_archive_status(self, fname: str, fsize: int) -> FileStatus:
        """Check, is there already in DB a parsed file or no.

        Args:
            fname (str): File name.
            fsize (int): File size.

        Returns:
            FileStatus: Result.
        """

        self.log.debug(f"Check, is there parsed file {fname} or no")
        sess = self._session()
        arch = aliased(Archive, name="arch")
        query = sess.query(arch)

        archive = query.filter(arch.name == fname,
                               arch.size == fsize).one_or_none()

        sess.close()

        return self._compare_fdata_and_return(archive, fsize)

    def get_archive(self, fname: str, fsize: int) -> Archive:
        """Get archive information from DB.s

        Args:
            fname (str): File(archive) name.
            fsize (int): Archive size.

        Returns:
            models.Archive: Archive data.
        """
        sess = self._session()
        query = sess.query(Archive)

        archive = query.filter(Archive.name == fname,
                               Archive.size == fsize).first()
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
            int: new archive ID.
        """

        self.log.debug(f"Add info about a new archive {fname} to database")
        sess = self._session()
        archive = Archive(name=fname, size=fsize, law_number=law_number, folder_name=folder_name)
        sess.add(archive)
        sess.commit()

        archive_id = archive.id
        sess.close()

        return archive_id

    def mark_archive_as_parsed(self, archive_id: int, reason="OK"):
        """Mark archive as parsed with reason. Default reason is `OK`.
        Reason 'OK' means that everything is good, all archive files were parsed and load successfully.

        Args:
            archive_id (int): Archive ID
            reason (str, optional): Reason of marking. Defaults to "OK".
        """

        self.log.debug(f"Mark archive with ID {archive_id} as parsed")
        sess = self._session()

        archive = sess.query(Archive).filter_by(id=archive_id).first()
        archive.has_parsed = True
        archive.parsed_on = dt.utcnow()
        archive.reason = reason
        sess.commit()
        sess.close()

    def update_archive(self, archive_id: int, **kwargs):
        """Update archive info.

        Args:
            archive_id (int): Archive ID
        """

        self.log.debug(f"Update archive with ID {archive_id}")
        sess = self._session()
        sess.query(Archive).filter_by(id=archive_id).update(kwargs)
        sess.commit()
        sess.close()

    def add_archive_file(self, archive_id: int, fname: str, fsize: int) -> int:
        """Add information about archive's file to DB.

        Args:
            archive_id (int): Archive ID.
            fname (str): File name.
            fsize (int): File size.

        Returns:
            int: ID of a new file.
        """

        self.log.debug(f"Add info to database about a new file {fname} inside archive")
        sess = self._session()

        file = ArchiveFile(archive_id=archive_id, name=fname, size=fsize)
        sess.add(file)
        sess.commit()

        file_id = file.id
        sess.close()

        return file_id

    def get_archive_file_status(self, archive_id: int, fname: str, fsize: int) -> FileStatus:
        self.log.debug(f"Check, is there parsed file {fname} or no")
        sess = self._session()
        query = sess.query(ArchiveFile)
        file = query.filter(ArchiveFile.name == fname,
                            ArchiveFile.archive_id == archive_id,
                            ArchiveFile.size == fsize).one_or_none()

        sess.close()
        return self._compare_fdata_and_return(file, fsize)

    def get_archive_file(self, archive_id: int, fname: str, fsize: int) -> ArchiveFile:
        sess = self._session()
        query = sess.query(ArchiveFile)
        file = query.filter(ArchiveFile.name == fname,
                            ArchiveFile.archive_id == archive_id,
                            ArchiveFile.size == fsize).first()

        sess.close()
        return file

    def mark_archive_file_as_parsed(self, file_id: int, xml_type: str, session=None, reason=None):
        """Mark archive file as parsed.

        Args:
            file_id (int): File ID.
            xml_type (str): Type of XML, `protocol` or `notification`.
            session (sessionmarket, optional): DB session. Defaults to None.
            reason (str, optional): Reason of parsed file. Defaults to None.
        """
        sess = session if session is not None else self._session()
        file = sess.query(ArchiveFile).filter_by(id=file_id).first()
        file.has_parsed = True
        file.parsed_on = dt.utcnow()
        file.reason = reason
        file.xml_type = xml_type
        if session is None:
            sess.commit()
            sess.close()

    def delete_archive_files(self, archive_id: int):
        """Delete files of an archive by archive ID.

        Args:
            archive_id (int): Archive ID.
        """
        sess = self._session()
        sess.query(ArchiveFile).filter(ArchiveFile.archive_id == archive_id).delete()
        sess.commit()
        sess.close()

    def get_session(self):
        return self._session()
