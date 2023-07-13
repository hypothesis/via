import json
from json import JSONDecodeError
from logging import getLogger
from urllib.parse import urlencode

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


class YouTubeAPIV3CredBased:
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

    def __init__(self, credentials_list):
        """Initialise the service.

        :param credentials_list: A list of dicts of credentials info as
            provided by Google console's JSON format.

        :raises ConfigurationError: If the credentials are not accepted by Google
        """
        if credentials_list[0].get("disable"):
            LOG.error("Google Drive credentials have been disabled")
            return

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

    def list_captions(self, video_id):
        # https://developers.google.com/youtube/v3/docs/captions/list
        data = self._request(
            "GET",
            "/captions",
            query=(
                ("part", "id"),
                ("part", "snippet"),
                ("videoId", video_id),
            ),
        )

        return [
            {
                "id": item["id"],
                "language": item["snippet"]["language"],
                "name": item["snippet"]["name"],
                "kind": item["snippet"]["trackKind"],
            }
            for item in data["items"]
        ]

    def get_caption(self, caption_id):
        data = self._request("GET", f"/captions/{caption_id}")

        # ??? Now what? Haven't seen it work

        return data

    _URL_STUB = "https://youtube.googleapis.com/youtube/v3"

    def _request(self, method, path, query=None):
        url = self._URL_STUB + "/" + path.lstrip("/")
        if query:
            query += "?" + urlencode(query)

        return self._http_service.request(
            method=method,
            url=url,
            headers=add_request_headers(
                {
                    "Accept": "application/json",
                    "Accept-Encoding": "gzip, deflate",
                    "User-Agent": "(gzip)",
                }
            ),
            timeout=self.TIMEOUT,
            max_allowed_time=self.TIMEOUT,
        ).json()


class YouTubeAPIV3KeyBased:
    def __init__(self, api_key: str):
        self._api_key = api_key
        self._http = HTTPService()

    _API_STUB = "https://youtube.googleapis.com/youtube/v3"

    def list_captions(self, video_id):
        # https://developers.google.com/youtube/v3/docs/captions/list
        response = self._http.get(
            url=self._make_url(
                "/captions",
                (
                    ("part", "id"),
                    ("part", "snippet"),
                    ("videoId", video_id),
                    ("key", self._api_key),
                ),
            ),
            headers={"Accept": "application/json"},
        )

        data = response.json()

        return [
            {
                "id": item["id"],
                "language": item["snippet"]["language"],
                "name": item["snippet"]["name"],
                "kind": item["snippet"]["trackKind"],
            }
            for item in data["items"]
        ]

    def download_caption(self, caption_id):
        response = self._http.get(
            url=self._make_url(f"/captions/{caption_id}", (("key", self._api_key),)),
            headers={"Accept": "application/json"},
        )

        data = response.json()

        return data

    def _make_url(self, path, query):
        url = self._API_STUB + path
        url += "?" + urlencode(query)

        return url


with open(".devdata/google_drive_credentials.json") as handle:
    creds = json.load(handle)

client = YouTubeAPIV3CredBased(creds)
# client = YouTubeAPIV3KeyBased(api_key='NOPE')


for caption in client.list_captions("rSTqpRYzJbo"):
    print(caption)
    print(client.download_caption(caption_id=caption["id"]))
    exit()
