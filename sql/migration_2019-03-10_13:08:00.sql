INSERT INTO forty_fourth_law.tags_to_fields_dict VALUES ('notificationAttachments', 'notification_attachments');
ALTER TABLE forty_fourth_law.notifications_rare_tags ADD notification_attachments JSONB;

UPDATE
    forty_fourth_law.notifications_rare_tags 
SET notification_attachments = subquery.value
FROM (
    SELECT archive_file_id, value
    FROM forty_fourth_law.notifications_unknown_tags
    WHERE name = 'notificationAttachments' ) AS subquery
WHERE forty_fourth_law.notifications_rare_tags.archive_file_id = subquery.archive_file_id;

INSERT INTO
    forty_fourth_law.notifications_rare_tags (archive_file_id, notification_attachments)
    SELECT ut.archive_file_id, ut.value
    FROM forty_fourth_law.notifications_unknown_tags ut
    WHERE
        ut.name = 'notificationAttachments' AND
        ut.archive_file_id NOT IN (SELECT archive_file_id FROM forty_fourth_law.notifications_rare_tags);

DELETE FROM forty_fourth_law.notifications_unknown_tags WHERE name = 'notificationAttachments';