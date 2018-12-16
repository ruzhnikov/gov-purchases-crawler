
# -*- coding: utf-8 -*-

"""Class that contains description of SQLAlchemy tables"""

import sqlalchemy as sa
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import JSONB


_Base = declarative_base()


class Archive(_Base):
    """Table `archive`
    """
    __tablename__ = "archives"

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String, nullable=False)
    size = sa.Column(sa.Integer, nullable=False)
    downloaded_on = sa.Column(sa.DateTime, nullable=False, server_default=sa.text("NOW() AT TIME ZONE 'utc'"))
    parsed_on = sa.Column(sa.DateTime, nullable=True)
    has_parsed = sa.Column(sa.Boolean, nullable=False, default=False)


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


class FFLNotificationOftenTags(_Base):
    __tablename__ = "notifications_often_tags"
    __table_args__ = ({"schema": "forty_fourth_law"})

    id = sa.Column(sa.Integer, primary_key=True)
    archive_file_id = sa.Column(sa.Integer, sa.ForeignKey("archive_files.id"))
    purchase_number = sa.Column(sa.String(20), nullable=True)
    purchase_id = sa.Column(sa.INT, nullable=True)
    doc_publish_date = sa.Column(sa.DATETIME, nullable=True)
    href = sa.Column(sa.String(100), nullable=True)
    print_form = sa.Column(JSONB, nullable=True)
    purchase_object_info = sa.Column(sa.String, nullable=True)
    placing_way = sa.Column(JSONB, nullable=True)
    purchase_responsible = sa.Column(JSONB, nullable=True)
    lot = sa.Column(JSONB, nullable=True)
    attachments = sa.Column(JSONB, nullable=True)
    procedure_info = sa.Column(JSONB, nullable=True)
    version_number = sa.Column(sa.String(20), nullable=True)
    lot_number = sa.Column(sa.String(20), nullable=True)
    foundation_protocol_number = sa.Column(sa.String(40), nullable=True)
    create_date = sa.Column(sa.DATETIME, nullable=True)
    procedurel_failed = sa.Column(sa.String(20), nullable=True)
    result = sa.Column(sa.String(20), nullable=True)
    etp = sa.Column(JSONB, nullable=True)
    currency = sa.Column(JSONB, nullable=True)
    number = sa.Column(sa.String(40), nullable=True)
    sign_date = sa.Column(sa.DATE, nullable=True)
    foundation = sa.Column(JSONB, nullable=True)
    customer = sa.Column(JSONB, nullable=True)
    price = sa.Column(sa.String(20), nullable=True)
    conclude_contract_right = sa.Column(sa.String(20), nullable=True)
    protocol_date = sa.Column(sa.DATE, nullable=True)
    suppliers = sa.Column(JSONB, nullable=True)
    applications = sa.Column(JSONB, nullable=True)
    price_rur = sa.Column(sa.String(20), nullable=True)
    doc_number = sa.Column(sa.String(80), nullable=True)
    direct_date = sa.Column(sa.DATETIME, nullable=True)
    abandoned_reason = sa.Column(JSONB, nullable=True)
    external_id = sa.Column(sa.String(40), nullable=True)
    contract_service_info = sa.Column(sa.String, nullable=True)
    note = sa.Column(sa.String, nullable=True)


class FFLNotificationRareTags(_Base):
    __tablename__ = "notifications_rare_tags"
    __table_args__ = ({"schema": "forty_fourth_law"})

    id = sa.Column(sa.Integer, primary_key=True)
    archive_file_id = sa.Column(sa.Integer, sa.ForeignKey("archive_files.id"))
    modification = sa.Column(JSONB, nullable=True)
    topic = sa.Column(sa.String, nullable=True)
    request_number = sa.Column(sa.String(40), nullable=True)
    question = sa.Column(sa.String, nullable=True)
    doc_type = sa.Column(JSONB, nullable=True)
    purchase_documentation = sa.Column(JSONB, nullable=True)
    doc_date = sa.Column(sa.DATETIME, nullable=True)
    lots = sa.Column(JSONB, nullable=True)
    cancel_reason = sa.Column(JSONB, nullable=True)
    add_info = sa.Column(sa.String, nullable=True)
    contract_conclusion_on_st83_ch2 = sa.Column(sa.String(20), nullable=True)
    particulars_act_procurement = sa.Column(sa.String, nullable=True)
    common_info = sa.Column(JSONB, nullable=True)
    attachments_info = sa.Column(JSONB, nullable=True)
    print_form_info = sa.Column(JSONB, nullable=True)
    purchase_responsible_info = sa.Column(JSONB, nullable=True)
    notification_info = sa.Column(JSONB, nullable=True)
    placing_way_info = sa.Column(JSONB, nullable=True)
    collecting_end_date = sa.Column(sa.DATETIME, nullable=True)
    collecting_prolongation_date = sa.Column(sa.DATETIME, nullable=True)
    is_goz = sa.Column(sa.String(20), nullable=True)
    opening_date = sa.Column(sa.DATETIME, nullable=True)
    opening_prolongation_date = sa.Column(sa.DATETIME, nullable=True)
    base_change = sa.Column(JSONB, nullable=True)
    notif_resp_org = sa.Column(JSONB, nullable=True)
    purchase = sa.Column(JSONB, nullable=True)
    previous_resp_org = sa.Column(JSONB, nullable=True)
    new_resp_org = sa.Column(JSONB, nullable=True)
    article15_features_info = sa.Column(sa.String(20), nullable=True)
    notification_cancel_info = sa.Column(sa.String(100), nullable=True)
    recovery_to_stage = sa.Column(sa.String(20), nullable=True)
    notification_cancel_failure_org = sa.Column(JSONB, nullable=True)
    ext_print_form = sa.Column(JSONB, nullable=True)
    auction_time = sa.Column(sa.String(40), nullable=True)
    new_auction_date = sa.Column(sa.DATETIME, nullable=True)
    reason = sa.Column(JSONB, nullable=True)
    modification_info = sa.Column(JSONB, nullable=True)
    protocol_lot = sa.Column(JSONB, nullable=True)
    scoring_date = sa.Column(sa.DATETIME, nullable=True)
    scoring_prolongation_date = sa.Column(sa.DATETIME, nullable=True)
    print_form_fields_info = sa.Column(JSONB, nullable=True)
    cancel_reason_info = sa.Column(JSONB, nullable=True)
    procedure_ok_info = sa.Column(JSONB, nullable=True)
    procedure_okou_info = sa.Column(JSONB, nullable=True)
    responsible_org = sa.Column(JSONB, nullable=True)
    responsible_role = sa.Column(sa.String(20), nullable=True)
    responsible_info = sa.Column(JSONB, nullable=True)
    code = sa.Column(sa.String(20), nullable=True)
    name = sa.Column(sa.String(80), nullable=True)
    max_price = sa.Column(sa.String(20), nullable=True)
    finance_source = sa.Column(sa.String(40), nullable=True)
    quantity_undefined = sa.Column(sa.String(20), nullable=True)
    customer_requirements = sa.Column(JSONB, nullable=True)
    purchase_objects = sa.Column(JSONB, nullable=True)
    restrict_info = sa.Column(sa.String(20), nullable=True)
    documentation = sa.Column(JSONB, nullable=True)
    prolongation_info = sa.Column(JSONB, nullable=True)
    note = sa.Column(sa.String, nullable=True)


class FFLNotificationUnknownTags(_Base):
    __tablename__ = "notifications_unknown_tags"
    __table_args__ = ({"schema": "forty_fourth_law"})

    id = sa.Column(sa.Integer, primary_key=True)
    archive_file_id = sa.Column(sa.Integer, sa.ForeignKey("archive_files.id"))
    name = sa.Column(sa.String(100), nullable=True)
    value = sa.Column(JSONB, nullable=True)
    note = sa.Column(sa.String, nullable=True)


class FFLTagsToFieldsDict(_Base):
    __tablename__ = "tags_to_fields_dict"
    __table_args__ = ({"schema": "forty_fourth_law"})

    tag = sa.Column(sa.String(100), nullable=False, primary_key=True)
    field = sa.Column(sa.String(150), nullable=False, primary_key=True)
