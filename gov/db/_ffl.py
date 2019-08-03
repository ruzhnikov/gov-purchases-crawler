
from ._db import DBClient
from .models import FFLProtocolsData, FFLNotificationsData


class FortyFourthLawDB(DBClient):
    """Class for working with DB for 44th law
    """

    def insert_protocol_data(self, file_id: int, data: dict, session=None):
        sess = session if session is not None else self._session()
        file_data = FFLProtocolsData(archive_file_id=file_id, data=data)
        sess.add(file_data)

        if session is None:
            sess.commit()
            sess.close()

    def insert_notification_data(self, file_id: int, data: dict, session=None):
        sess = session if session is not None else self._session()
        file_data = FFLNotificationsData(archive_file_id=file_id, data=data)
        sess.add(file_data)

        if session is None:
            sess.commit()
            sess.close()

    def delete_file_data(self, file_id: int):
        """Delete all rows related with file_id from all forty_fourth_law.* tables

        Args:
            file_id (int): ID of XML file.
        """

        sess = self._session()
        for table in (FFLProtocolsData, FFLNotificationsData):
            sess.query(table).filter(table.archive_file_id == file_id).delete()
        sess.commit()
        sess.close()
