"""Retrieve details about a resource at a URL."""
import cgi
import re
from functools import wraps

import requests
from requests import RequestException

from via.exceptions import (
    REQUESTS_BAD_URL,
    REQUESTS_UPSTREAM_SERVICE,
    BadURL,
    UnhandledException,
    UpstreamServiceError,
)
from via.get_url.headers import clean_headers

GOOGLE_DRIVE_REGEX = re.compile(
    r"^https://drive.google.com/uc\?id=(.*)&export=download$", re.IGNORECASE
)


def _handle_errors(inner):
    """Translate errors into our application errors."""

    @wraps(inner)
    def deco(*args, **kwargs):
        try:
            return inner(*args, **kwargs)

        except REQUESTS_BAD_URL as err:
            raise BadURL(err.args[0]) from None

        except REQUESTS_UPSTREAM_SERVICE as err:
            raise UpstreamServiceError(err.args[0]) from None

        except RequestException as err:
            raise UnhandledException(err.args[0]) from None

    return deco


@_handle_errors
def get_url_details(url, headers=None):
    """Get the content type and status code for a given URL.

    :param url: URL to retrieve
    :param headers: The original headers the request was made with
    :return: 2-tuple of (mime type, status code)

    :raise BadURL: When the URL is malformed
    :raise UpstreamServiceError: If we server gives us errors
    :raise UnhandledException: For all other request based errors
    """
    if headers is None:
        headers = {}

    if GOOGLE_DRIVE_REGEX.match(url):
        return "application/pdf", 200

    with requests.get(
        url,
        stream=True,
        allow_redirects=True,
        headers=clean_headers(headers),
        timeout=10,
    ) as rsp:
        content_type = rsp.headers.get("Content-Type")
        if content_type:
            mime_type, _ = cgi.parse_header(content_type)
        else:
            mime_type = None

        return mime_type, rsp.status_code
