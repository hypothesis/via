"""Retrieve details about a resource at a URL."""
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
def get_url_details(url):
    """Get the content type and status code for a given URL.

    :param url: URL to retrieve
    :return: 2-tuple of (content type, status code)

    :raise BadURL: When the URL is malformed
    :raise UpstreamServiceError: If we server gives us errors
    :raise UnhandledException: For all other request based errors
    """

    if GOOGLE_DRIVE_REGEX.match(url):
        return "application/pdf", 200

    with requests.get(url, stream=True, allow_redirects=True) as rsp:
        return rsp.headers.get("Content-Type"), rsp.status_code
