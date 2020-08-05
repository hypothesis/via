"""View for redirecting based on content type."""

from urllib.parse import parse_qsl, urlencode, urlparse

from pyramid import httpexceptions as exc
from pyramid import view
from webob.multidict import MultiDict

from via.get_url import get_url_details


@view.view_config(route_name="route_by_content")
def route_by_content(context, request):
    """Routes the request according to the Content-Type header."""
    mime_type, status_code = get_url_details(context.url(), request.headers)

    # Can PDF mime types get extra info on the end like "encoding=?"
    if mime_type in ("application/x-pdf", "application/pdf"):
        # Unless we have some very baroque error messages they shouldn't
        # really be returning PDFs

        redirect_url = request.route_url("view_pdf", _query=request.params)

        return exc.HTTPFound(redirect_url, headers=_caching_headers(max_age=300))

    # redirect_url = _get_legacy_via_url(request)
    redirect_url = request.route_url("view_html", _query=request.params)
    headers = _cache_headers_for_http(status_code)

    return exc.HTTPFound(redirect_url, headers=headers)


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


def _caching_headers(max_age, stale_while_revalidate=86400):
    # I tried using webob.CacheControl for this but it's total rubbish
    header = (
        f"public, max-age={max_age}, stale-while-revalidate={stale_while_revalidate}"
    )
    return {"Cache-Control": header}
