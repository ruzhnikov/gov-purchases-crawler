
# -*- coding: utf-8 -*-

import logging
from ftplib import FTP
from .errors import EmptyDownloadDirError

_FTP_LOGIN = "free"
_FTP_PASSWORD = "free"
_FTP_ROOT_DIR = "/fcs_regions"
_PATH_DATA = {
    "region": None,
    "folders_chain": [],
    "folder_files": [],
    "last_file": None
}

# a folder in a region directory. A region data will be downloaded from this folder.
_DEFAULT_SERVER_FOLDER = "notifications"


class Client():
    """Class for working with FTP server"""

    def __init__(self, server_address: str, logger: logging.RootLogger, server_folder=_DEFAULT_SERVER_FOLDER):
        self._server = server_address
        self._server_folder = server_folder
        self._log = logger
        self._regions = []
        self._skipped_region = None
        self._download_dir = None
        self._is_connected = False
        self._connect()

    def _connect(self):
        """Connect and auth on the FTP server"""

        self._log.debug(f"Connect to server {self._server}")
        self._ftp = FTP(self._server)
        self._ftp.login(_FTP_LOGIN, _FTP_PASSWORD)
        self._is_connected = True
        self._log.debug("Successfully")

    def set_download_dir(self, new_dir: str):
        """Set local folder for doanloading files for the client.s

        Args:
            new_dir (str): Folder name.
        """

        self._log.debug(f"Set directory {new_dir} as folder for downloading archives")
        self._download_dir = new_dir

    def reconnect(self):
        pass

    def set_region_skipped(self, region: str):
        """Mark a region as is needed to skip.

        Args:
            region (str): Region name.
        """
        self._skipped_region = region

    def read(self):
        pass

    def download(self, fpath: str, fname: str, download_dir=None):
        """Download an archive file from mentioned folder of server.

        Args:
            fpath (str): Archive file on the server with absolute path to the file.
            fname (str): Archive file name.
            download_dir (str, optional): Defaults to None. Directory for downloading.

        Raises:
            EmptyDownloadDirError: There is no folder for downloading file.
        """

        if download_dir is None:
            if self._download_dir is None:
                raise EmptyDownloadDirError
            download_dir = self._download_dir

        path_to_download = download_dir + "/" + fname
        self._ftp.retrbinary(f"RETR {fpath}", open(path_to_download, "wb").write)

    @property
    def regions(self):
        """Get regions list.

        Returns:
            [str]: List of regions.
        """
        return self._regions
