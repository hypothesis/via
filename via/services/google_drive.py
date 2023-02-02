import re
from json import JSONDecodeError
from logging import getLogger
from typing import ByteString, Iterator
from urllib.parse import parse_qs, urlparse

from google.auth.transport.requests import AuthorizedSession
from google.oauth2.service_account import Credentials
from marshmallow import INCLUDE, Schema, ValidationError, fields, validate
from pyramid.httpexceptions import HTTPNotFound
from requests import HTTPError

from via.exceptions import ConfigurationError, GoogleDriveServiceError
from via.requests_tools import add_request_headers
from via.services.http import HTTPService

LOG = getLogger(__name__)


class GoogleDriveErrorSchema(Schema):
    """Schema for the JSON bodies of Google Drive error responses."""

    class Meta:
        unknown = INCLUDE

    class Errors(Schema):
        errors = fields.List(
            fields.Dict(), required=True, validate=validate.Length(min=1)
        )

    error = fields.Nested(Errors(unknown=INCLUDE), required=True)


_GOOGLE_ERROR_MAP = {
    (403, "userRateLimitExceeded"): {
        "message": "Too many concurrent requests to the Google Drive API",
        # 429 - Too many requests
        # Not 100% accurate as the user probably isn't making too many, but
        # close enough as it conveys the need to back off
        "status_int": 429,
    },
    (403, "cannotDownloadFile"): {
        # This seems to happen if a file is locked down in various ways
        # rather than for general consumption
        "message": "We do not have permission to download the file through the"
        " Google Drive API",
        "status_int": 403,
    },
    (403, "cannotDownloadAbusiveFile"): {
        "message": "Google has identified this file as malicious and has "
        "denied access to it",
        # 423 - Locked
        # 'The resource that is being accessed is locked' - kinda?
        "status_int": 423,
    },
}


def translate_google_error(error):
    """Get a specific error instance from the provided error or None."""

    if not isinstance(error, HTTPError) or error.response is None:
        return None

    status_code = error.response.status_code

    try:
        validated_data = GoogleDriveErrorSchema().load(error.response.json())
    except (JSONDecodeError, ValidationError):
        return None

    google_message = validated_data["error"]["errors"][0].get("message")
    google_reason = validated_data["error"]["errors"][0].get("reason")

    # Check carefully to see that this is Google telling us the file isn't
    # found rather than this being us going to the wrong end-point
    if status_code == 404 and google_reason == "notFound":
        return HTTPNotFound(str(google_message) or "File id not found")

    if settings := _GOOGLE_ERROR_MAP.get((status_code, google_reason)):
        return GoogleDriveServiceError(**settings, requests_err=error)

    return None


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

    def __init__(self, credentials_list, resource_keys):
        """Initialise the service.

        :param credentials_list: A list of dicts of credentials info as
            provided by Google console's JSON format.
        :param resource_keys: A dict of file ids to resource keys, to fill out
            any missing resource keys.

        :raises ConfigurationError: If the credentials are not accepted by Google
        """
        if credentials_list[0].get("disable"):
            LOG.error("Google Drive credentials have been disabled")
            return

        self._resource_keys = resource_keys

        try:
            credentials = Credentials.from_service_account_info(
                credentials_list[0], scopes=self.SCOPES
            )
        except ValueError as exc:
            raise ConfigurationError(
                "The Google Drive service account information is invalid"
            ) from exc

        self._http_service = HTTPService(
            session=AuthorizedSession(credentials, refresh_timeout=self.TIMEOUT),
            error_translator=translate_google_error,
        )

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

    def iter_file(self, file_id, resource_key=None) -> Iterator[ByteString]:
        """Get a generator of chunks of bytes for the specified file.

        :param file_id: Google Drive file id to retrieve
        :param resource_key: Google Drive resources key (if any)
        :returns: A generator of byte strings which taken together form the
            document

        :raises HTTPNotFound: If the file id is not valid
        :raises GoogleDriveServiceError: For specifically handled scenarios
            like timeouts and rate limiting
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

        yield from self._http_service.stream(
            url=url,
            headers=headers,
            timeout=self.TIMEOUT,
            max_allowed_time=self.TIMEOUT,
        )
