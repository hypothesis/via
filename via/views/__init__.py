"""The views for the Pyramid app."""
from via.resources import URLResource


def add_routes(config):
    """Add routes to pyramid config."""
    config.add_route("get_status", "/_status")
    config.add_route("view_pdf", "/pdf", factory=URLResource)

    config.add_route("view_html", "/html", factory=URLResource)
    config.add_route("view_js", "/js", factory=URLResource)
    config.add_route("view_css", "/css", factory=URLResource)

    config.add_route("route_by_content", "/route", factory=URLResource)


def includeme(config):
    """Pyramid config."""
    add_routes(config)
    config.scan(__name__)
