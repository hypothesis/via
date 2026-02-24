"""View for redirecting based on content type."""

from h_vialib import ContentType
from pyramid import httpexceptions as exc
from pyramid import view

from via.services import SecureLinkService, URLDetailsService, ViaClientService


@view.view_config(route_name="route_by_content")
def route_by_content(context, request):
    """Routes the request according to the Content-Type header.

    If the request comes through LMS (has a valid signed URL), serve the
    original routing logic. Otherwise, show the restricted access page.
    """
    secure_link_service = request.find_service(SecureLinkService)

    if not secure_link_service.request_is_valid(request):
        try:
            target_url = context.url_from_query()
        except Exception:  # noqa: BLE001
            target_url = None

        request.override_renderer = "via:templates/restricted.html.jinja2"
        return {"target_url": target_url}

    url = context.url_from_query()

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
        return _caching_headers(max_age=60)

    if status_code < 500:
        return _caching_headers(max_age=60)

    return {"Cache-Control": "no-cache"}


def _caching_headers(max_age, stale_while_revalidate=86400):
    header = (
        f"public, max-age={max_age}, stale-while-revalidate={stale_while_revalidate}"
    )
    return {"Cache-Control": header}
