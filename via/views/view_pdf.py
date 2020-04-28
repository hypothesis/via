"""View presenting the PDF viewer."""
import json

from markupsafe import Markup
from pyramid import view

from via.configuration import Configuration


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

    _, h_config = Configuration.extract_from_params(request.params)

    return {
        "pdf_url": _string_literal(pdf_url),
        "client_embed_url": _string_literal(
            request.registry.settings["client_embed_url"]
        ),
        "static_url": request.static_url,
        "hypothesis_config": h_config,
    }


def _string_literal(string):
    """Return a JSON escaped, but otherwise un-modified string."""

    return Markup(json.dumps(str(string)))
