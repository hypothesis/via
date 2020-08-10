"""View for redirecting based on content type."""

from pyramid import httpexceptions as exc
from pyramid import view

from via.get_url import get_url_details
from via.services.html_rewriter import html_rewriter_factory


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

    url = html_rewriter_factory(request).url_for(request.params)
    headers = _cache_headers_for_http(status_code)

    return exc.HTTPFound(url, headers=headers)


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


def _caching_headers(max_age, stale_while_revalidate=86400):
    # I tried using webob.CacheControl for this but it's total rubbish
    header = (
        f"public, max-age={max_age}, stale-while-revalidate={stale_while_revalidate}"
    )
    return {"Cache-Control": header}
