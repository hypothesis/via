from pyramid.httpexceptions import HTTPGone
from pyramid.view import view_config

from via.services import SecureLinkService, URLDetailsService, ViaClientService


@view_config(route_name="static_fallback")
def static_fallback(_context, _request):
    """Make sure we don't try to proxy out of date static content."""

    raise HTTPGone("It appears you have requested out of date content")  # noqa: EM101, TRY003


@view_config(
    route_name="proxy",
    renderer="via:templates/proxy.html.jinja2",
)
def proxy(context, request):
    """Proxy view.

    If the request comes through LMS (valid signed URL), serve the proxy.
    Otherwise, show the restricted access page.
    """
    secure_link_service = request.find_service(SecureLinkService)

    if not secure_link_service.request_is_valid(request):
        try:
            target_url = context.url_from_path()
        except Exception:  # noqa: BLE001
            target_url = None
        request.override_renderer = "via:templates/restricted.html.jinja2"
        return {"target_url": target_url}

    url = context.url_from_path()

    mime_type, _status_code = request.find_service(URLDetailsService).get_url_details(
        url
    )

    return {
        "src": request.find_service(ViaClientService).url_for(
            url, mime_type, request.params
        )
    }
