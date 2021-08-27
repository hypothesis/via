import json
import os
import re
from io import BytesIO

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload
from pyramid.httpexceptions import HTTPNotFound

from via.exceptions import ConfigurationError, UpstreamServiceError


class GoogleDriveAPI:
    SCOPES = [
        # If we want metadata
        "https://www.googleapis.com/auth/drive.metadata.readonly",
        # To actually get the file
        "https://www.googleapis.com/auth/drive.readonly",
    ]

    def __init__(self, service_account_info):
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

    @classmethod
    def from_credentials_file(cls, credentials_file):
        if not os.path.isfile(credentials_file):
            raise FileNotFoundError(
                f"Could not find specified credentials file: '{credentials_file}'"
            )

        with open(credentials_file, encoding="utf-8") as handle:
            # We expect an array of credentials, but for the moment, only with
            # one entry. This is for potential round robin-ing later
            return cls(service_account_info=json.load(handle)[0])

    @property
    def is_available(self):
        """Get whether the Google Drive API is available."""

        return self._service is not None

    _PUBLIC_URL_REGEX = re.compile(
        r"^https://drive.google.com/uc\?id=(.*)&export=download$", re.IGNORECASE
    )

    @classmethod
    def google_drive_id(cls, public_url):
        if match := cls._PUBLIC_URL_REGEX.match(public_url):
            return match.group(1)

        return None

    def iter_file(self, file_id):
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
                message = http_error.error_details[0]["message"]
            except (IndexError, KeyError):
                message = "File not found"

            raise HTTPNotFound(message) from http_error

        raise UpstreamServiceError(
            "Error experienced using Google Drive API"
        ) from http_error


def factory(_context, request):
    if credentials_file := request.registry.settings.get(
        "google_drive_credentials_file"
    ):
        return GoogleDriveAPI.from_credentials_file(credentials_file)

    return GoogleDriveAPI(service_account_info=None)
