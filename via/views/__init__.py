"""The views for the Pyramid app."""
from via.resources import URLResource


def add_routes(config):  # pragma: no cover
    """Add routes to pyramid config."""

    config.add_route("index", "/", factory=URLResource)
    config.add_route("get_status", "/_status")
    config.add_route("view_pdf", "/pdf", factory=URLResource)
    config.add_route("route_by_content", "/route", factory=URLResource)
    config.add_route("debug_headers", "/debug/headers")
    config.add_route("proxy_google_drive_file", "/google_drive/{file_id}/proxied.pdf")
    config.add_route(
        "proxy_google_drive_file:resource_key",
        "/google_drive/{file_id}/{resource_key}/proxied.pdf",
    )
    config.add_route("proxy", "/{url:.*}", factory=URLResource)


def includeme(config):  # pragma: no cover
    """Pyramid config."""

    add_routes(config)
    config.scan(__name__)
