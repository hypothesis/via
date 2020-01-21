"""The views for the Pyramid app."""
import urllib

import pyramid.httpexceptions as exc
import requests
from pyramid import response, view
from pyramid.settings import asbool

# Client configuration query parameters.
OPEN_SIDEBAR = "via.open_sidebar"
CONFIG_FROM_FRAME = "via.request_config_from_frame"


@view.view_config(renderer="py_proxy:templates/index.html.jinja2", route_name="index")
def index(_request):
    """Index endpoint."""
    return {}


@view.view_config(route_name="status")
def status(_request):
    """Status endpoint."""
    return response.Response(status_int=200, status="200 OK", content_type="text/plain")


@view.view_config(route_name="robots", http_cache=(86400, {"public": True}))
def robots(request):
    """Serve robots.txt file."""
    return response.FileResponse(
        "py_proxy/static/robots.txt", request=request, content_type="text/plain"
    )


@view.view_config(route_name="favicon", http_cache=(86400, {"public": True}))
def favicon(request):
    """Serve favicon.ico file."""
    return response.FileResponse(
        "py_proxy/static/favicon.ico", request=request, content_type="image/x-icon"
    )


@view.view_config(
    renderer="py_proxy:templates/pdfjs_viewer.html.jinja2", route_name="pdf"
)
def pdf(request):
    """HTML page with client and the PDF embedded."""
    nginx_server = request.registry.settings["nginx_server"]
    pdf_url = _generate_url_without_client_query_params(
        request.matchdict["pdf_url"], request.params
    )

    return {
        "pdf_url": f"{nginx_server}/proxy/static/{pdf_url}",
        "client_embed_url": request.registry.settings["client_embed_url"],
        "h_open_sidebar": asbool(request.params.get(OPEN_SIDEBAR, False)),
        "h_request_config": request.params.get(CONFIG_FROM_FRAME, None),
    }


@view.view_config(route_name="content_type")
def content_type(request):
    """Routes the request according to the Content-Type header."""
    url = _generate_url_without_client_query_params(
        request.matchdict["url"], request.params
    )

    with requests.get(url, stream=True, allow_redirects=True) as rsp:
        if rsp.headers.get("Content-Type") in ("application/x-pdf", "application/pdf",):
            return exc.HTTPFound(
                request.route_url(
                    "pdf", pdf_url=request.matchdict["url"], _query=request.params
                )
            )
    via_url = request.registry.settings["legacy_via_url"]
    url = _drop_from_url_begining("/", request.path_qs)
    return exc.HTTPFound(f"{via_url}/{url}")


def _drop_from_url_begining(drop_chars, url):
    """Drop drop_chars from begining of url."""
    drop_before = len(drop_chars)
    return url[drop_before:]


def _generate_url_without_client_query_params(base_url, query_params):
    """Return ``base_url`` with non-Via params from ``query_params`` appended.

    Return ``base_url`` with all the non-Via query params from ``query_params``
    appended to it as a query string. Any params in ``query_params`` that are
    meant for Via (the ``"via.*`` query params) will be ignored and *not*
    appended to the returned URL.

    :param base_url: the protocol, domain and path, for example: https://thirdparty.url/foo.pdf
    :type base_url: str

    :param query_params: the query params to be added to base_url
    :type query_params: dict

    :return: ``base_url`` with the non-Via query params appended
    :rtype: str
    """
    client_params = [OPEN_SIDEBAR, CONFIG_FROM_FRAME]
    filtered_params = urllib.parse.urlencode(
        {
            param: value
            for param, value in query_params.items()
            if param not in client_params
        }
    )
    if filtered_params:
        return f"{base_url}?{filtered_params}"
    return base_url


def add_routes(config):
    """Add routes to pyramid config."""
    config.add_route("index", "/")
    config.add_route("status", "/_status")
    config.add_route("favicon", "/favicon.ico")
    config.add_route("robots", "/robots.txt")
    config.add_route("pdf", "/pdf/{pdf_url:.*}")
    config.add_route("content_type", "/{url:.*}")


def includeme(config):
    """Pyramid config."""
    add_routes(config)
    config.scan(__name__)
