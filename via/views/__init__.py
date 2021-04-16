"""The views for the Pyramid app."""
from via.resources import URLResource


def add_routes(config):
    """Add routes to pyramid config."""
    config.add_route("index", "/")
    config.add_route("get_status", "/_status")
    config.add_route("view_pdf", "/pdf", factory=URLResource)
    config.add_route("route_by_content", "/route", factory=URLResource)
    config.add_route("debug_headers", "/debug/headers")
    config.add_route("proxy", "/{url:.*}")


def includeme(config):
    """Pyramid config."""
    add_routes(config)
    config.scan(__name__)
