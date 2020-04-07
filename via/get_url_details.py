"""Retrieve details about a resource at a URL."""
import os
import re
from functools import wraps
from json import JSONDecodeError

import requests
from requests import RequestException

from via.exceptions import (
    REQUESTS_BAD_URL,
    REQUESTS_UPSTREAM_SERVICE,
    BadURL,
    UnhandledException,
    UpstreamServiceError,
)

GOOGLE_DRIVE_REGEX = re.compile(
    r"^https://drive.google.com/uc\?id=(.*)&export=download$", re.IGNORECASE
)
GOOGLE_DRIVE_API_KEY = os.environ.get("GOOGLE_DRIVE_API_KEY")
GOOGLE_DRIVE_URL = "https://www.googleapis.com/drive/v3/files/"


def _handle_errors(inner):
    """Translate errors into our application errors."""

    @wraps(inner)
    def deco(*args, **kwargs):
        try:
            return inner(*args, **kwargs)

        except REQUESTS_BAD_URL as err:
            raise BadURL(err.args[0]) from None

        except JSONDecodeError as err:
            raise UpstreamServiceError(err.args[0]) from None

        except REQUESTS_UPSTREAM_SERVICE as err:
            raise UpstreamServiceError(err.args[0]) from None

        except RequestException as err:
            raise UnhandledException(err.args[0]) from None

    return deco


@_handle_errors
def get_url_details(url):
    """Get the content type and status code for a given URL.

    :param url: URL to retrieve
    :return: 2-tuple of (content type, status code)

    :raise BadURL: When the URL is malformed
    :raise UpstreamServiceError: If we server gives us errors
    :raise UnhandledException: For all other request based errors
    """

    google_drive = GOOGLE_DRIVE_REGEX.match(url)
    if google_drive:
        if not GOOGLE_DRIVE_API_KEY:
            return "application/pdf", 200

        rsp = requests.get(
            f"{GOOGLE_DRIVE_URL}{google_drive.group(1)}?key={GOOGLE_DRIVE_API_KEY}"
        )
        data = rsp.json()

        return data["mimeType"], rsp.status_code

    with requests.get(url, stream=True, allow_redirects=True) as rsp:
        return rsp.headers.get("Content-Type"), rsp.status_code
