import json
import re
from json import JSONDecodeError
from typing import ByteString, Iterator

from google.auth.transport.requests import AuthorizedSession
from google.oauth2.service_account import Credentials

from via.exceptions import ConfigurationError
from via.requests_tools import add_request_headers, stream_bytes
from via.requests_tools.error_handling import iter_handle_errors


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

            self._session = AuthorizedSession(credentials)
        else:
            self._session = None

    @property
    def is_available(self):
        """Get whether the Google Drive API is available."""

        return self._session is not None

    _PUBLIC_URL_REGEX = re.compile(
        r"^https://drive.google.com/uc\?id=(.*)&export=download$", re.IGNORECASE
    )

    @classmethod
    def google_drive_id(cls, public_url):
        """Extract the google drive ID from a URL if there is one."""

        if match := cls._PUBLIC_URL_REGEX.match(public_url):
            return match.group(1)

        return None

    @iter_handle_errors
    def iter_file(self, file_id) -> Iterator[ByteString]:
        """Get a generator of chunks of bytes for the specified file.

        :param file_id: Google Drive file id to retrieve
        :returns: A generator of byte strings which taken together form the
            document

        :raises HTTPNotFound: If the file id is not valid
        :raises UpstreamServiceError: For other errors
        """
        # https://developers.google.com/drive/api/v3/reference/files/get
        url = f"https://www.googleapis.com/drive/v3/files/{file_id}?alt=media"

        headers = add_request_headers(
            {
                "Accept": "*/*",
                "Accept-Encoding": "gzip, deflate",
                "User-Agent": "(gzip)",
            }
        )

        response = self._session.get(url=url, headers=headers, stream=True, timeout=10)
        response.raise_for_status()

        yield from stream_bytes(response)


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
