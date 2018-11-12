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
    archive_id INT REFERENCES archives (id),
    name VARCHAR (250) NOT NULL,
    size INT NOT NULL,
    parsed_on TIMESTAMP WITHOUT TIME ZONE DEFAULT NULL,
    has_parsed BOOLEAN NOT NULL DEFAULT FALSE
);