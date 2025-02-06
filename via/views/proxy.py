from pyramid.httpexceptions import HTTPGone
from pyramid.view import view_config

from via.services import URLDetailsService, ViaClientService, has_secure_url_token


@view_config(route_name="static_fallback")
def static_fallback(_context, _request):
    """Make sure we don't try to proxy out of date static content."""

    raise HTTPGone("It appears you have requested out of date content")  # noqa: EM101, TRY003


@view_config(
    route_name="proxy",
    renderer="via:templates/proxy.html.jinja2",
    decorator=(has_secure_url_token,),
)
def proxy(context, request):
    url = context.url_from_path()

    mime_type, _status_code = request.find_service(URLDetailsService).get_url_details(
        url
    )

    return {
        "src": request.find_service(ViaClientService).url_for(
            url, mime_type, request.params
        )
    }
