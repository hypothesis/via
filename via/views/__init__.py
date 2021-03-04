"""The views for the Pyramid app."""
from pyramid.view import view_config

from via.resources import URLResource


def add_routes(config):
    """Add routes to pyramid config."""
    config.add_route("get_status", "/_status")
    config.add_route("view_pdf", "/pdf", factory=URLResource)
    config.add_route("route_by_content", "/route", factory=URLResource)
    config.add_route("debug_headers", "/debug/headers")
    config.add_route("foo", "/{fizzle:.*}")


def includeme(config):
    """Pyramid config."""
    add_routes(config)
    config.scan(__name__)


@view_config(route_name="foo", renderer="via:templates/foo.html.jinja2")
def foo(request):
    return {"src": request.route_url("route_by_content", _query={"url": request.path[1:]})}
