"""View for redirecting based on content type."""

from pyramid import httpexceptions as exc
from pyramid import view

from via.get_url import get_url_details
from via.services import ViaClientService
from via.views.decorators import checkmate_block, has_secure_url_token


@view.view_config(
    route_name="route_by_content", decorator=(checkmate_block, has_secure_url_token)
)
def route_by_content(context, request):
    """Routes the request according to the Content-Type header."""
    mime_type, status_code = get_url_details(context.url(), request.headers)

    # Can PDF mime types get extra info on the end like "encoding=?"
    if mime_type in ("application/x-pdf", "application/pdf"):
        # Unless we have some very baroque error messages they shouldn't
        # really be returning PDFs
        content_type, caching_headers = "pdf", _caching_headers(max_age=300)
    else:
        content_type, caching_headers = "html", _cache_headers_for_http(status_code)

    # The via client will handle the URL correctly for us, we don't want to
    # include it as a param in case we are going to ViaHTML. All other params
    # should be passed on
    options = dict(request.params)
    options.pop("url")
    if request.registry.settings["checkmate_enabled"]:
        # Checkmate check already done, no need to keep passing this
        options.pop("via.blocked_for", None)

    via_client = request.find_service(ViaClientService)
    url = via_client.url_for(context.url(), content_type=content_type, options=options)

    return exc.HTTPFound(url, headers=caching_headers)


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
