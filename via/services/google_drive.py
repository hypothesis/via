import re
from json import JSONDecodeError
from logging import getLogger
from typing import ByteString, Iterator
from urllib.parse import parse_qs, urlparse

from google.auth.transport.requests import AuthorizedSession
from google.oauth2.service_account import Credentials
from pyramid.httpexceptions import HTTPNotFound
from requests import HTTPError

from via.exceptions import ConfigurationError
from via.requests_tools import add_request_headers, stream_bytes
from via.requests_tools.error_handling import iter_handle_errors

LOG = getLogger(__name__)


class GoogleDriveAPI:
    """Simplified interface for interacting with Google Drive."""

    SCOPES = [
        # If we want metadata
        "https://www.googleapis.com/auth/drive.metadata.readonly",
        # To actually get the file
        "https://www.googleapis.com/auth/drive.readonly",
    ]

    # Configure all the various types of timeout available to us, with the hope
    # that the shortest one will kick in first
    TIMEOUT = 30

    def __init__(self, credentials_list=None, resource_keys=None):
        """Initialise the service.

        :param credentials_list: A list of dicts of credentials info as
            provided by Google console's JSON format.
        :param resource_keys: A dict of file ids to resource keys, to fill out
            any missing resource keys.

        :raises ConfigurationError: If the credentials are not accepted by Google
        """
        self._resource_keys = resource_keys or {}

        if credentials_list:
            try:
                credentials = Credentials.from_service_account_info(
                    credentials_list[0], scopes=self.SCOPES
                )
            except ValueError as exc:
                raise ConfigurationError(
                    "The Google Drive service account information is invalid"
                ) from exc

            self._session = AuthorizedSession(credentials, refresh_timeout=self.TIMEOUT)
        else:
            self._session = None

    @property
    def is_available(self):
        """Get whether the Google Drive API is available."""

        return self._session is not None

    _FILE_PATH_REGEX = re.compile("/file/d/(?P<file_id>[^/]+)")

    @classmethod
    def parse_file_url(cls, public_url):
        """Extract the Google Drive data from a URL if there is one.

        :param public_url: URL to parse
        :return: A dict of details if this is a Google Drive file URL or None
        """

        if not public_url.startswith("https://drive.google.com"):
            return None

        url = urlparse(public_url)
        if "/folders" in url.path:
            return None

        query = {key.lower(): value for key, value in parse_qs(url.query).items()}

        if match := cls._FILE_PATH_REGEX.search(url.path):
            data = match.groupdict()
        elif file_id := query.get("id"):
            data = {"file_id": file_id[0]}
        else:
            return None

        data["resource_key"] = query.get("resourcekey", [None])[0]

        return data

    # Pylint doesn't understand our error translation
    # pylint:disable=missing-raises-doc
    @iter_handle_errors
    def iter_file(self, file_id, resource_key=None) -> Iterator[ByteString]:
        """Get a generator of chunks of bytes for the specified file.

        :param file_id: Google Drive file id to retrieve
        :param resource_key: Google Drive resources key (if any)
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

        if not resource_key:
            # If we are being called, we should have been initialised with a
            # set of resource keys. See the factory below
            resource_key = self._resource_keys.get(file_id)
            if resource_key:
                LOG.info(
                    "Mapped Google Drive file id '%s' to resource key '%s'",
                    file_id,
                    resource_key,
                )

        if resource_key:
            headers["X-Goog-Drive-Resource-Keys"] = f"{file_id}/{resource_key}"

        response = self._session.get(
            url=url,
            headers=headers,
            stream=True,
            timeout=self.TIMEOUT,
            max_allowed_time=self.TIMEOUT,
        )
        try:
            response.raise_for_status()

        except HTTPError as http_error:
            # Pylint thinks we are raising None here, but the if takes care
            # of that
            # pylint: disable=raising-bad-type
            if translated_error := self._translate_http_error(http_error, file_id):
                raise translated_error from http_error

            raise

        yield from stream_bytes(response)

    @classmethod
    def _translate_http_error(cls, http_error, file_id):
        if http_error.response is None:
            return None

        google_error = cls._get_google_error(http_error)

        # Check carefully to see that this is Google telling us the file isn't
        # found rather than this being us going to the wrong end-point
        if (
            http_error.response.status_code == 404
            and google_error
            and google_error.get("reason") == "notFound"
        ):
            return HTTPNotFound(f"File id {file_id} not found")

        return None

    @classmethod
    def _get_google_error(cls, http_error):
        try:
            return http_error.response.json()["error"]["errors"][0]

        except (JSONDecodeError, KeyError):
            return None
