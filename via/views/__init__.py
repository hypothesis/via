"""The views for the Pyramid app."""
from via.resources import PathURLResource, QueryURLResource


def add_routes(config):  # pragma: no cover
    """Add routes to pyramid config."""

    config.add_route("index", "/", factory=QueryURLResource)
    config.add_route("get_status", "/_status")
    config.add_route("view_pdf", "/pdf", factory=QueryURLResource)
    config.add_route("view_video", "/video", factory=QueryURLResource)
    config.add_route("route_by_content", "/route", factory=QueryURLResource)
    config.add_route("debug_headers", "/debug/headers")
    config.add_route(
        "proxy_google_drive_file",
        "/google_drive/{file_id}/proxied.pdf",
        factory=QueryURLResource,
    )
    config.add_route(
        "proxy_google_drive_file:resource_key",
        "/google_drive/{file_id}/{resource_key}/proxied.pdf",
        factory=QueryURLResource,
    )
    config.add_route(
        "proxy_onedrive_pdf", "/onedrive/proxied.pdf", factory=QueryURLResource
    )
    config.add_route("proxy_d2l_pdf", "/d2l/proxied.pdf", factory=QueryURLResource)
    config.add_route("proxy_python_pdf", "proxied.pdf", factory=QueryURLResource)

    config.add_route("proxy", "/{url:.*}", factory=PathURLResource)


def includeme(config):  # pragma: no cover
    """Pyramid config."""

    add_routes(config)
    config.scan(__name__)
