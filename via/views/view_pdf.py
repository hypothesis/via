"""View presenting the PDF viewer."""

from pyramid import view
from pyramid.settings import asbool

from via.views._query_params import QueryParams


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
    pdf_url = QueryParams.build_url(
        request.matchdict["pdf_url"], request.params, strip_via_params=True
    )

    return {
        "pdf_url": f"{nginx_server}/proxy/static/{pdf_url}",
        "client_embed_url": request.registry.settings["client_embed_url"],
        "h_open_sidebar": asbool(request.params.get(QueryParams.OPEN_SIDEBAR, False)),
        "h_request_config": request.params.get(QueryParams.CONFIG_FROM_FRAME, None),
        "static_url": request.static_url,
    }
