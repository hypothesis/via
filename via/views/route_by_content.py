"""View for redirecting based on content type."""

from h_vialib import ContentType
from pyramid import httpexceptions as exc
from pyramid import view

from via.services import URLDetailsService, ViaClientService, has_secure_url_token


@view.view_config(route_name="route_by_content", decorator=(has_secure_url_token,))
def route_by_content(context, request):
    """Routes the request according to the Content-Type header."""
    url = context.url_from_query()

    request.checkmate.raise_if_blocked(url)

    mime_type, status_code = request.find_service(URLDetailsService).get_url_details(
        url, request.headers
    )
    via_client_svc = request.find_service(ViaClientService)

    if via_client_svc.content_type(mime_type) in (ContentType.PDF, ContentType.YOUTUBE):
        caching_headers = _caching_headers(max_age=300)
    else:
        caching_headers = _cache_headers_for_http(status_code)

    params = dict(request.params)
    params.pop("url", None)

    url = via_client_svc.url_for(url, mime_type, params)

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
