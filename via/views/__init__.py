"""The views for the Pyramid app."""
from via.resources import URLRoute


def add_routes(config):
    """Add routes to pyramid config."""
    config.add_route("get_status", "/_status")
    config.add_route("view_pdf", "/pdf", factory=URLRoute)
    config.add_route("route_by_content", "/route", factory=URLRoute)


def includeme(config):
    """Pyramid config."""
    add_routes(config)
    config.scan(__name__)
