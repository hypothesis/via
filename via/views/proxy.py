from pyramid.view import view_config

from via.get_url import get_url_details
from via.services import ViaClientService


@view_config(route_name="proxy", renderer="via:templates/proxy.html.jinja2")
def proxy(context, request):
    url = context.url_from_path()
    request.checkmate.raise_if_blocked(url)

    mime_type, _status_code = get_url_details(url)

    return {
        "src": request.find_service(ViaClientService).url_for(
            url, mime_type, request.params
        )
    }
