"""The views for the Pyramid app."""
import pyramid.httpexceptions as exc
import requests
from pyramid import response, view


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
    pdf_url = _drop_from_url_begining("/pdf/", request.path_qs)

    return {
        "pdf_url": f"{nginx_server}/proxy/static/{pdf_url}",
        "client_embed_url": request.registry.settings["client_embed_url"],
        "h_open_sidebar": int(request.params.get("via.open_sidebar", "0")),
        "h_request_config": request.params.get("via.request_config_from_frame", None),
    }


@view.view_config(route_name="content_type")
def content_type(request):
    """Routes the request according to the Content-Type header."""
    url = _drop_from_url_begining("/", request.path_qs)

    with requests.get(url, stream=True, allow_redirects=True) as rsp:
        if rsp.headers.get("Content-Type") in ("application/x-pdf", "application/pdf",):
            return exc.HTTPFound(request.route_url("pdf", pdf_url=url))
    via_url = request.registry.settings["legacy_via_url"]
    return exc.HTTPFound(f"{via_url}/{url}")


def _drop_from_url_begining(drop_chars, url):
    """Drop drop_chars from begining of url."""
    drop_before = len(drop_chars)
    return url[drop_before:]


def includeme(config):
    """Pyramid config."""
    config.add_route("index", "/")
    config.add_route("status", "/_status")
    config.add_route("favicon", "/favicon.ico")
    config.add_route("robots", "/robots.txt")
    config.add_route("pdf", "/pdf/{pdf_url:.*}")
    config.add_route("content_type", "/{url:.*}")
    config.scan(__name__)
