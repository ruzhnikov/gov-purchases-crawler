
# -*- coding: utf-8 -*-

"""Class that contains description of SQLAlchemy tables"""

import sqlalchemy as sa
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import ENUM


_Base = declarative_base()


class Archive(_Base):
    """Table `archives`
    """
    __tablename__ = "archives"

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String, nullable=False)
    size = sa.Column(sa.Integer, nullable=False)
    downloaded_on = sa.Column(sa.DateTime, nullable=False, server_default=sa.text("NOW() AT TIME ZONE 'utc'"))
    parsed_on = sa.Column(sa.DateTime, nullable=True)
    has_parsed = sa.Column(sa.Boolean, nullable=False, default=False)
    law_number = sa.Column(ENUM("44", "223", name="law"), nullable=False, default="44")
    folder_name = sa.Column(sa.String(100), nullable=False)


class ArchiveFile(_Base):
    """Table `archive_files`
    """
    __tablename__ = "archive_files"

    id = sa.Column(sa.Integer, primary_key=True)
    archive_id = sa.Column(sa.Integer, sa.ForeignKey("archives.id"))
    name = sa.Column(sa.String, nullable=False)
    xml_type = sa.Column("type", sa.String(100), nullable=True)
    size = sa.Column(sa.Integer, nullable=False)
    parsed_on = sa.Column(sa.DateTime, nullable=True)
    has_parsed = sa.Column(sa.Boolean, nullable=False, default=False)
    reason = sa.Column(sa.String(250), nullable=True)

    archives = relationship("Archive")
