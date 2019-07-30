
from ._db import DBClient
from .models import FFLProtocolsData, FFLNotificationsData


class FortyFourthLawDB(DBClient):
    """Class for working with DB of 44th law
    """

    def insert_protocol_data(self, file_id: int, data: dict):
        pass

    def insert_notification_data(self, file_id: int, data: dict):
        pass

    def delete_file_data(self, file_id: int):
        """Delete all rows related with file_id from all forty_fourth_law.* tables

        Args:
            file_id (int): ID of XML file.
        """

        sess = self.session()
        for table in (FFLProtocolsData, FFLNotificationsData):
            sess.query(table).filter(table.archive_file_id == file_id).delete()
        sess.commit()
        sess.close()
