"""View for redirecting based on content type."""

import os
import re
from datetime import datetime
from logging import getLogger
from urllib.parse import parse_qsl, urlencode, urlparse

import requests
from pyramid import httpexceptions as exc
from pyramid import view
from requests import RequestException
from webob.multidict import MultiDict

from via.exceptions import (
    REQUESTS_BAD_URL,
    REQUESTS_UPSTREAM_SERVICE,
    BadURL,
    UnhandledException,
    UpstreamServiceError,
)

LOG = getLogger(__name__)


@view.view_config(route_name="route_by_content")
def route_by_content(request):
    """Routes the request according to the Content-Type header."""
    path_url = request.params["url"]

    start = datetime.utcnow()

    mime_type, status_code = _get_url_details(path_url)

    diff = datetime.utcnow() - start
    diff = diff.seconds * 1000 + diff.microseconds / 1000
    print(f"Got URL: '{path_url}' in {diff}ms")

    # Can PDF mime types get extra info on the end like "encoding=?"
    if mime_type in ("application/x-pdf", "application/pdf"):
        # Unless we have some very baroque error messages they shouldn't
        # really be returning PDFs

        redirect_url = request.route_url("view_pdf", _query=request.params)

        return exc.HTTPFound(redirect_url, headers=_caching_headers(max_age=300))

    via_url = _get_legacy_via_url(request)
    headers = _cache_headers_for_http(status_code)

    return exc.HTTPFound(via_url, headers=headers)


def _cache_headers_for_http(status_code):
    if status_code == 404:
        # 404 - A rare case we may want to handle differently, as unusually
        # for a 4xx error, trying again can help if it becomes available
        return _caching_headers(max_age=60)

    if status_code < 500:
        # 2xx - OK
        # 3xx - we follow it, so this shouldn't happen
        # 4xx - no point in trying again quickly
        return _caching_headers(max_age=60)

    # 5xx - Errors should not be cached
    return {"Cache-Control": "no-cache"}


def _get_legacy_via_url(request):
    # Get the query we were called with and remove the url
    query = MultiDict(request.params)
    raw_url = urlparse(query.pop("url"))

    # Create a legacy via URL by concatenating the urls
    via_url = request.registry.settings["legacy_via_url"]
    bare_url = raw_url._replace(query=None).geturl()
    via_url = urlparse(f"{via_url}/{bare_url}")

    # Add the merged query parameters
    query.update(parse_qsl(raw_url.query))
    via_url = via_url._replace(query=urlencode(query))

    return via_url.geturl()


GOOGLE_DRIVE_REGEX = re.compile(
    "^https://drive.google.com/uc\?id=(.*)&export=download$", re.IGNORECASE
)
GOOGLE_DRIVE_API_KEY = os.environ.get("GOOGLE_DRIVE_API_KEY")


def _get_url_details(url):
    is_google_drive = GOOGLE_DRIVE_REGEX.match(url)

    try:
        if is_google_drive:
            file_id = is_google_drive.group(1)

            url = f"https://www.googleapis.com/drive/v3/files/{file_id}?key={GOOGLE_DRIVE_API_KEY}"
            rsp = requests.get(url)
            data = rsp.json()

            return data["mimeType"], rsp.status_code

        else:
            with requests.get(url, stream=True, allow_redirects=True) as rsp:
                return rsp.headers.get("Content-Type"), rsp.status_code

    except REQUESTS_BAD_URL as err:
        raise BadURL(err.args[0]) from None

    except REQUESTS_UPSTREAM_SERVICE as err:
        raise UpstreamServiceError(err.args[0]) from None

    except RequestException as err:
        raise UnhandledException(err.args[0]) from None


def _caching_headers(max_age, stale_while_revalidate=86400):
    # I tried using webob.CacheControl for this but it's total rubbish
    header = (
        f"public, max-age={max_age}, stale-while-revalidate={stale_while_revalidate}"
    )
    return {"Cache-Control": header}
