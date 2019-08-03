CREATE TYPE law AS ENUM ('44', '223');

-- the main table for storing archives
DROP TABLE IF EXISTS archives CASCADE;
CREATE TABLE archives (
    id SERIAL PRIMARY KEY,
    name VARCHAR(250) NOT NULL,
    size INT NOT NULL,
    downloaded_on TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'utc'),
    parsed_on TIMESTAMP WITHOUT TIME ZONE DEFAULT NULL,
    updated_on TIMESTAMP WITHOUT TIME ZONE DEFAULT NULL,
    has_parsed boolean NOT NULL DEFAULT FALSE,
    law_number law NOT NULL DEFAULT '44',
    folder_name VARCHAR(100),
    reason VARCHAR(250) DEFAULT 'OK'
);

-- table for storing files of archive
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

-- a table for storing file's data of notifications in JSONB format
DROP TABLE IF EXISTS forty_fourth_law.notifications_data;
CREATE TABLE forty_fourth_law.notifications_data (
    id SERIAL PRIMARY KEY,
    archive_file_id INT REFERENCES archive_files (id) ON DELETE CASCADE,
    data JSONB
);

-- a table for storing file's data of protocols in JSONB format
DROP TABLE IF EXISTS forty_fourth_law.protocols_data;
CREATE TABLE forty_fourth_law.protocols_data (
    id SERIAL PRIMARY KEY,
    archive_file_id INT REFERENCES archive_files (id) ON DELETE CASCADE,
    data JSONB
);
