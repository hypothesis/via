"""View for redirecting based on content type."""

from h_vialib.secure.url import ViaSecureURL
from pyramid import httpexceptions as exc
from pyramid import view

from via.get_url import get_url_details
from via.views.decorators import has_secure_url_token
from via.views.route_by_content._html_rewriter import HTMLRewriter


@view.view_config(route_name="route_by_content", decorator=has_secure_url_token)
def route_by_content(context, request):
    """Routes the request according to the Content-Type header."""
    mime_type, status_code = get_url_details(context.url(), request.headers)

    # Can PDF mime types get extra info on the end like "encoding=?"
    if mime_type in ("application/x-pdf", "application/pdf"):
        # Unless we have some very baroque error messages they shouldn't
        # really be returning PDFs

        # Re-sign for the new URL
        signed_via_pdf_url = ViaSecureURL(
            request.registry.settings["via_secret"]
        ).create(request.route_url("view_pdf", _query=request.params))

        return exc.HTTPFound(signed_via_pdf_url, headers=_caching_headers(max_age=300))

    url = HTMLRewriter.from_request(request).url_for(request.params)
    return exc.HTTPFound(url, headers=_cache_headers_for_http(status_code))


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
