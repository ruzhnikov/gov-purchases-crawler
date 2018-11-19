DROP TABLE IF EXISTS archives;
CREATE TABLE archives (
    id SERIAL PRIMARY KEY,
    name VARCHAR(250) NOT NULL,
    name_with_path VARCHAR(500) NOT NULL,
    size INT NOT NULL,
    downloaded_on TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'utc'),
    parsed_on TIMESTAMP WITHOUT TIME ZONE DEFAULT NULL,
    updated_on TIMESTAMP WITHOUT TIME ZONE DEFAULT NULL,
    has_parsed boolean NOT NULL DEFAULT FALSE,
    UNIQUE(name_with_path)
);

DROP TABLE IF EXISTS archive_files;
CREATE TABLE archive_files (
    id SERIAL PRIMARY KEY,
    archive_id INT REFERENCES archives (id) ON DELETE CASCADE,
    name VARCHAR(250) NOT NULL,
    size INT NOT NULL,
    parsed_on TIMESTAMP WITHOUT TIME ZONE DEFAULT NULL,
    has_parsed BOOLEAN NOT NULL DEFAULT FALSE
);

DROP TABLE IF EXISTS fourty_fourth_law_content;
CREATE TABLE fourty_fourth_law_content (
    id SERIAL PRIMARY KEY,
    archive_file_id INT REFERENCES archive_files (id) ON DELETE CASCADE,
    purchase_number VARCHAR(100),
    href VARCHAR(500),
    purchase_object_info TEXT,
    placing_way JSONB,
    etp JSONB,
    purchase_responsible JSONB,
    procedure_info JSONB,
    lot JSONB
);
