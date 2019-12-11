"""The views for the Pyramid app."""
from pyramid import response, view


@view.view_config(renderer="py_proxy:templates/index.html.jinja2", route_name="index")
def index(_request):
    """Index endpoint."""
    return {}


@view.view_config(route_name="status")
def status(_request):
    """Status endpoint."""
    return response.Response(status_int=200, status="200 OK", content_type="text/plain")


def includeme(config):
    """Pyramid config."""
    config.add_route("index", "/")
    config.add_route("status", "/_status")
    config.scan(__name__)
