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

# The Chrome user-agent as of 24/06/2020
BACKUP_USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "snap Chromium/83.0.4103.106 Chrome/83.0.4103.106 Safari/537.36"
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
def get_url_details(url, headers):
    """Get the content type and status code for a given URL.

    :param url: URL to retrieve
    :param headers: The original headers the request was made with
    :return: 2-tuple of (content type, status code)

    :raise BadURL: When the URL is malformed
    :raise UpstreamServiceError: If we server gives us errors
    :raise UnhandledException: For all other request based errors
    """

    if GOOGLE_DRIVE_REGEX.match(url):
        return "application/pdf", 200

    with requests.get(
        url,
        stream=True,
        allow_redirects=True,
        headers={"User-Agent": headers.get("User-Agent", BACKUP_USER_AGENT)},
    ) as rsp:
        return rsp.headers.get("Content-Type"), rsp.status_code
