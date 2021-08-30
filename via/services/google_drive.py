import json
import re
from io import BytesIO
from json import JSONDecodeError
from typing import ByteString, Iterator

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload
from pyramid.httpexceptions import HTTPNotFound

from via.exceptions import ConfigurationError, UpstreamServiceError


class GoogleDriveAPI:
    """Simplified interface for interacting with Google Drive."""

    SCOPES = [
        # If we want metadata
        "https://www.googleapis.com/auth/drive.metadata.readonly",
        # To actually get the file
        "https://www.googleapis.com/auth/drive.readonly",
    ]

    def __init__(self, service_account_info):
        """Initialise the service.

        :param service_account_info: A dict of credentials info as provided by
            Google console's JSON format.

        :raises ConfigurationError: If the credentials are not accepted by Google
        """
        if service_account_info:
            try:
                credentials = Credentials.from_service_account_info(
                    service_account_info, scopes=self.SCOPES
                )
            except ValueError as exc:
                raise ConfigurationError(
                    "The Google Drive service account information is invalid"
                ) from exc

            self._service = build("drive", "v3", credentials=credentials)
        else:
            self._service = None

    @property
    def is_available(self):
        """Get whether the Google Drive API is available."""

        return self._service is not None

    _PUBLIC_URL_REGEX = re.compile(
        r"^https://drive.google.com/uc\?id=(.*)&export=download$", re.IGNORECASE
    )

    @classmethod
    def google_drive_id(cls, public_url):
        """Extract the google drive ID from a URL if there is one."""

        if match := cls._PUBLIC_URL_REGEX.match(public_url):
            return match.group(1)

        return None

    def iter_file(self, file_id) -> Iterator[ByteString]:
        """Get a generator of chunks of bytes for the specified file.

        :param file_id: Google Drive file id to retrieve
        :returns: A generator of byte strings which taken together form the
            document

        :raises HTTPNotFound: If the file id is not valid
        :raises UpstreamServiceError: For other errors
        """
        # https://developers.google.com/drive/api/v3/manage-downloads#download_a_file_stored_on_google_drive
        # pylint: disable=no-member
        request = self._service.files().get_media(fileId=file_id)

        handle = BytesIO()
        downloader = MediaIoBaseDownload(handle, request)
        done = False
        while not done:
            try:
                _status, done = downloader.next_chunk()
            except HttpError as exc:
                self._raise_translated_error(exc)

            yield handle.getvalue()
            handle.truncate(0)

    @staticmethod
    def _raise_translated_error(http_error):
        if http_error.status_code == 404:
            try:
                # Is this always the case? It seems like Google errors don't
                # have a fixed format by looking at the code to generate them.
                message = http_error.error_details[0]["message"]
            except (IndexError, KeyError):
                message = "File not found"

            raise HTTPNotFound(message) from http_error

        raise UpstreamServiceError(
            "Error experienced using Google Drive API"
        ) from http_error


def factory(_context, request):
    if not request.registry.settings.get("google_drive_in_python"):
        return GoogleDriveAPI(service_account_info=None)

    credentials_json = request.registry.settings.get("google_drive_credentials")
    if not credentials_json:
        raise ConfigurationError(
            "The flag 'google_drive_in_python' is enabled but no credentials found"
        )

    try:
        return GoogleDriveAPI(service_account_info=json.loads(credentials_json))
    except JSONDecodeError as exc:
        raise ConfigurationError("Invalid Google credentials file format") from exc
