from pyramid.view import view_config

from via.get_url import get_url_details
from via.services import ViaClientService


@view_config(route_name="proxy", renderer="via:templates/proxy.html.jinja2")
def proxy(request):
    url = request.path[1:]  # Strip the leading "/" from the path.

    # Let people just type in "example.com" or link to
    # via.hypothes.is/example.com and have that proxy https://example.com.
    if not (url.startswith("http://") or url.startswith("https://")):
        url = "https://" + url

    mime_type, _status_code = get_url_details(url)

    return {
        "src": request.find_service(ViaClientService).url_for(
            url, mime_type, request.params
        )
    }
