ALTER TABLE archives ADD reason VARCHAR(250) DEFAULT 'OK';
UPDATE archives SET reason = NULL WHERE has_parsed = false;
