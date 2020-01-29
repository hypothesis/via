"""View for redirecting based on content type."""

import requests
from pyramid import httpexceptions as exc
from pyramid import view
from requests import RequestException

from via.exceptions import (
    REQUESTS_BAD_URL,
    REQUESTS_UPSTREAM_SERVICE,
    BadURL,
    UnhandledException,
    UpstreamServiceError,
)
# Client configuration query parameters.
from via.views.query_params import strip_client_query_params


@view.view_config(route_name="route_by_content")
def route_by_content(request):
    """Routes the request according to the Content-Type header."""
    url = strip_client_query_params(request.matchdict["url"], request.params)

    mime_type, status_code = _get_url_details(url)

    # Can PDF mime types get extra info on the end like "encoding=?"
    if mime_type in ("application/x-pdf", "application/pdf"):
        # Unless we have some very baroque error messages they shouldn't
        # really be returning PDFs
        return exc.HTTPFound(
            request.route_url(
                "view_pdf", pdf_url=request.matchdict["url"], _query=request.params,
            ),
            headers=_caching_headers(max_age=300),
        )

    if status_code == 404:
        # 404 - A rare case we may want to handle differently, as unusually
        # for a 4xx error, trying again can help if it becomes available
        headers = _caching_headers(max_age=60)

    elif status_code < 500:
        # 2xx - OK
        # 3xx - we follow it, so this shouldn't happen
        # 4xx - no point in trying again quickly
        headers = _caching_headers(max_age=60)

    else:
        # 5xx - Errors should not be cached
        headers = {"Cache-Control": "no-cache"}

    via_url = request.registry.settings["legacy_via_url"]
    url = request.path_qs.lstrip("/")

    return exc.HTTPFound(f"{via_url}/{url}", headers=headers)


def _get_url_details(url):
    try:
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
