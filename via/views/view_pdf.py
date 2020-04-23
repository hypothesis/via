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
def view_pdf(context, request):
    """HTML page with client and the PDF embedded."""

    nginx_server = request.registry.settings["nginx_server"]
    pdf_url = f"{nginx_server}/proxy/static/{context.url()}"

    return {
        "pdf_url": Markup(pdf_url),
        "client_embed_url": Markup(request.registry.settings["client_embed_url"]),
        "static_url": request.static_url,
        "hypothesis_config": _hypothesis_config(request),
    }


def _hypothesis_config(request):
    config = {"showHighlights": True, "appType": "via"}

    open_sidebar = asbool(request.params.get(_QueryParams.OPEN_SIDEBAR, False))
    if open_sidebar:
        config["openSidebar"] = True

    request_config = request.params.get(_QueryParams.CONFIG_FROM_FRAME, None)
    if request_config is not None:
        config["requestConfigFromFrame"] = request_config

    return config
