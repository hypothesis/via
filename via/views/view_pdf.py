"""View presenting the PDF viewer."""

from markupsafe import Markup
from pyramid import view
from pyramid.settings import asbool


class _QueryParams:
    """Client configuration query parameters."""

    # pylint: disable=too-few-public-methods

    OPEN_SIDEBAR = "via.open_sidebar"
    CONFIG_FROM_FRAME = "via.request_config_from_frame"


@view.view_config(
    renderer="via:templates/pdf_viewer.html.jinja2",
    route_name="view_pdf",
    # We have to keep the leash short here for caching so we can pick up new
    # immutable assets when they are deployed
    http_cache=0,
)
def view_pdf(request):
    """HTML page with client and the PDF embedded."""
    nginx_server = request.registry.settings["nginx_server"]
    pdf_url = request.params['url']

    return {
        "pdf_url": Markup(f"{nginx_server}/proxy/static/{pdf_url}"),
        "client_embed_url": Markup(request.registry.settings["client_embed_url"]),
        "h_open_sidebar": asbool(request.params.get(_QueryParams.OPEN_SIDEBAR, False)),
        "h_request_config": request.params.get(_QueryParams.CONFIG_FROM_FRAME, None),
        "static_url": request.static_url,
    }


