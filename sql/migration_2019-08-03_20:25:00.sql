DROP TABLE IF EXISTS forty_fourth_law.notifications_often_tags CASCADE;
DROP TABLE IF EXISTS forty_fourth_law.notifications_rare_tags CASCADE;
DROP TABLE IF EXISTS forty_fourth_law.notifications_unknown_tags CASCADE;
DROP TABLE IF EXISTS forty_fourth_law.protocols_often_tags CASCADE;
DROP TABLE IF EXISTS forty_fourth_law.protocols_rare_tags CASCADE;
DROP TABLE IF EXISTS forty_fourth_law.protocols_unknown_tags CASCADE;
DROP TABLE IF EXISTS forty_fourth_law.tags_to_fields_dict CASCADE;

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
