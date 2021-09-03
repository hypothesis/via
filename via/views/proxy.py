from h_vialib.configuration import Configuration
from pyramid.view import view_config

from via.get_url import get_url_details
from via.services import ViaClientService
from via.views._helpers import url_from_user_input


@view_config(route_name="proxy", renderer="via:templates/proxy.html.jinja2")
def proxy(request):
    # Strip leading '/' and normalize URL.
    url = url_from_user_input(request.path_qs[1:])
    url = Configuration.strip_from_url(url)

    request.checkmate.raise_if_blocked(url)

    mime_type, _status_code = get_url_details(url)

    return {
        "src": request.find_service(ViaClientService).url_for(
            url, mime_type, request.params
        )
    }
