DROP TABLE IF EXISTS archives CASCADE;
CREATE TABLE archives (
    id SERIAL PRIMARY KEY,
    name VARCHAR(250) NOT NULL,
    size INT NOT NULL,
    downloaded_on TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'utc'),
    parsed_on TIMESTAMP WITHOUT TIME ZONE DEFAULT NULL,
    updated_on TIMESTAMP WITHOUT TIME ZONE DEFAULT NULL,
    has_parsed boolean NOT NULL DEFAULT FALSE
);

DROP TABLE IF EXISTS archive_files CASCADE;
CREATE TABLE archive_files (
    id SERIAL PRIMARY KEY,
    archive_id INT REFERENCES archives (id) ON DELETE CASCADE,
    name VARCHAR(250) NOT NULL,
    type VARCHAR(100),
    size INT NOT NULL,
    parsed_on TIMESTAMP WITHOUT TIME ZONE DEFAULT NULL,
    has_parsed BOOLEAN NOT NULL DEFAULT FALSE,
    reason VARCHAR(250)
);

DROP SCHEMA IF EXISTS forty_fourth_law CASCADE;
CREATE SCHEMA forty_fourth_law;

DROP TABLE IF EXISTS forty_fourth_law.tags_to_fields_dict CASCADE;
CREATE TABLE forty_fourth_law.tags_to_fields_dict (
    tag varchar(100),
    field varchar(150)
);

INSERT INTO forty_fourth_law.tags_to_fields_dict VALUES
    ('purchaseNumber', 'purchase_number'),
    ('id', 'purchase_id'),
    ('docPublishDate', 'doc_publish_date'),
    ('href', 'href'),
    ('printForm', 'print_form'),
    ('purchaseObjectInfo', 'purchase_object_info'),
    ('placingWay', 'placing_way'),
    ('purchaseResponsible', 'purchase_responsible'),
    ('lot', 'lot'),
    ('attachments', 'attachments'),
    ('procedureInfo', 'procedure_info'),
    ('versionNumber', 'version_number'),
    ('lotNumber', 'lot_number'),
    ('foundationProtocolNumber', 'foundation_protocol_number'),
    ('createDate', 'create_date'),
    ('procedurelFailed', 'procedurel_failed'),
    ('result', 'result'),
    ('ETP', 'etp'),
    ('currency', 'currency'),
    ('number', 'number'),
    ('signDate', 'sign_date'),
    ('foundation', 'foundation'),
    ('customer', 'customer'),
    ('price', 'price'),
    ('concludeContractRight', 'conclude_contract_right'),
    ('protocolDate', 'protocol_date'),
    ('suppliers', 'suppliers'),
    ('applications', 'applications'),
    ('priceRUR', 'price_rur'),
    ('docNumber', 'doc_number'),
    ('directDate', 'direct_date'),
    ('abandonedReason', 'abandoned_reason'),
    ('externalId', 'external_id'),
    ('contractServiceInfo', 'contract_service_info'),
    ('modification', 'modification'),
    ('topic', 'topic'),
    ('requestNumber', 'request_number'),
    ('question', 'question'),
    ('docType', 'doc_type'),
    ('purchaseDocumentation', 'purchase_documentation'),
    ('docDate', 'doc_date'),
    ('lots', 'lots'),
    ('cancelReason', 'cancel_reason'),
    ('addInfo', 'add_info'),
    ('contractConclusionOnSt83Ch2', 'contract_conclusion_on_st83_ch2'),
    ('particularsActProcurement', 'particulars_act_procurement'),
    ('commonInfo', 'common_info'),
    ('attachmentsInfo', 'attachments_info'),
    ('printFormInfo', 'print_form_info'),
    ('purchaseResponsibleInfo', 'purchase_responsible_info'),
    ('notificationInfo', 'notification_info'),
    ('placingWayInfo', 'placing_way_info'),
    ('collectingEndDate', 'collecting_end_date'),
    ('collectingProlongationDate', 'collecting_prolongation_date'),
    ('isGOZ', 'is_goz'),
    ('openingDate', 'opening_date'),
    ('openingProlongationDate', 'opening_prolongation_date'),
    ('baseChange', 'base_change'),
    ('notifRespOrg', 'notif_resp_org'),
    ('purchase', 'purchase'),
    ('previousRespOrg', 'previous_resp_org'),
    ('newRespOrg', 'new_resp_org'),
    ('article15FeaturesInfo', 'article15_features_info'),
    ('notificationCancelInfo', 'notification_cancel_info'),
    ('recoveryToStage', 'recovery_to_stage'),
    ('notificationCancelFailureOrg', 'notification_cancel_failure_org'),
    ('extPrintForm', 'ext_print_form'),
    ('auctionTime', 'auction_time'),
    ('newAuctionDate', 'new_auction_date'),
    ('reason', 'reason'),
    ('modificationInfo', 'modification_info'),
    ('protocolLot', 'protocol_lot'),
    ('scoringDate', 'scoring_date'),
    ('scoringProlongationDate', 'scoring_prolongation_date'),
    ('printFormFieldsInfo', 'print_form_fields_info'),
    ('cancelReasonInfo', 'cancel_reason_info'),
    ('procedureOKInfo', 'procedure_ok_info'),
    ('procedureOKOUInfo', 'procedure_okou_info'),
    ('responsibleOrg', 'responsible_org'),
    ('responsibleRole', 'responsible_role'),
    ('responsibleInfo', 'responsible_info'),
    ('code', 'code'),
    ('name', 'name'),
    ('maxPrice', 'max_price'),
    ('financeSource', 'finance_source'),
    ('quantityUndefined', 'quantity_undefined'),
    ('customerRequirements', 'customer_requirements'),
    ('purchaseObjects', 'purchase_objects'),
    ('restrictInfo', 'restrict_info'),
    ('documentation', 'documentation'),
    ('prolongationInfo', 'prolongation_info');

DROP TABLE IF EXISTS forty_fourth_law.notifications_often_tags CASCADE;
CREATE TABLE forty_fourth_law.notifications_often_tags (
    id SERIAL PRIMARY KEY,
    archive_file_id INT REFERENCES archive_files (id) ON DELETE CASCADE,
    purchase_number VARCHAR(20),
    purchase_id VARCHAR(20),
    doc_publish_date TIMESTAMP WITH TIME ZONE,
    href VARCHAR(100),
    print_form JSONB,
    purchase_object_info TEXT,
    placing_way JSONB,
    purchase_responsible JSONB,
    lot JSONB,
    attachments JSONB,
    procedure_info JSONB,
    version_number VARCHAR(20),
    lot_number VARCHAR(20),
    foundation_protocol_number VARCHAR(40),
    create_date TIMESTAMP WITH TIME ZONE,
    procedurel_failed VARCHAR(20),
    result VARCHAR(20),
    etp JSONB,
    currency JSONB,
    number VARCHAR(40),
    sign_date DATE,
    foundation JSONB,
    customer JSONB,
    price VARCHAR(20),
    conclude_contract_right VARCHAR(20),
    protocol_date DATE,
    suppliers JSONB,
    applications JSONB,
    price_rur VARCHAR(20),
    doc_number VARCHAR(80),
    direct_date TIMESTAMP WITH TIME ZONE,
    abandoned_reason JSONB,
    external_id VARCHAR(40),
    contract_service_info TEXT
);

DROP TABLE IF EXISTS forty_fourth_law.notifications_rare_tags CASCADE;
CREATE TABLE forty_fourth_law.notifications_rare_tags (
    id SERIAL PRIMARY KEY,
    archive_file_id INT REFERENCES archive_files (id) ON DELETE CASCADE,
    modification JSONB,
    topic TEXT,
    request_number VARCHAR(40),
    question TEXT,
    doc_type JSONB,
    purchase_documentation JSONB,
    doc_date TIMESTAMP WITH TIME ZONE,
    lots JSONB,
    cancel_reason JSONB,
    add_info TEXT,
    contract_conclusion_on_st83_ch2 VARCHAR(20),
    particulars_act_procurement TEXT,
    common_info JSONB,
    attachments_info JSONB,
    print_form_info JSONB,
    purchase_responsible_info JSONB,
    notification_info JSONB,
    placing_way_info JSONB,
    collecting_end_date TIMESTAMP WITH TIME ZONE,
    collecting_prolongation_date TIMESTAMP WITH TIME ZONE,
    is_goz VARCHAR(20),
    opening_date TIMESTAMP WITH TIME ZONE,
    opening_prolongation_date TIMESTAMP WITH TIME ZONE,
    base_change JSONB,
    notif_resp_org JSONB,
    purchase JSONB,
    previous_resp_org JSONB,
    new_resp_org JSONB,
    article15_features_info VARCHAR(20),
    notification_cancel_info VARCHAR(100),
    recovery_to_stage VARCHAR(20),
    notification_cancel_failure_org JSONB,
    ext_print_form JSONB,
    auction_time VARCHAR(40),
    new_auction_date TIMESTAMP WITH TIME ZONE,
    reason JSONB,
    modification_info JSONB,
    protocol_lot JSONB,
    scoring_date TIMESTAMP WITH TIME ZONE,
    scoring_prolongation_date TIMESTAMP WITH TIME ZONE,
    print_form_fields_info JSONB,
    cancel_reason_info JSONB,
    procedure_ok_info JSONB,
    procedure_okou_info JSONB,
    responsible_org JSONB,
    responsible_role VARCHAR(20),
    responsible_info JSONB,
    code VARCHAR(20),
    name VARCHAR(80),
    max_price VARCHAR(20),
    finance_source VARCHAR(40),
    quantity_undefined VARCHAR(20),
    customer_requirements JSONB,
    purchase_objects JSONB,
    restrict_info VARCHAR(20),
    documentation JSONB,
    prolongation_info JSONB
);

DROP TABLE IF EXISTS forty_fourth_law.notifications_unknown_tags CASCADE;
CREATE TABLE forty_fourth_law.notifications_unknown_tags (
    id SERIAL PRIMARY KEY,
    archive_file_id INT REFERENCES archive_files (id) ON DELETE CASCADE,
    name VARCHAR(100),
    value JSONB
);
