"""A thin wrapper around ViaClient to make it a service."""
from h_vialib import ViaClient


class ViaClientService:
    """A wrapper service for h_vialib.ViaClient."""

    _mime_types_content_type = {
        "application/x-pdf": "pdf",
        "application/pdf": "pdf",
    }

    def content_type(self, mime_type):
        return self._mime_types_content_type.get(mime_type, "html")

    def __init__(self, via_client):
        self.via_client = via_client

    def url_for(self, url, mime_type, params):
        """Return a Via URL for the given `url`."""
        return self.via_client.url_for(
            url,
            content_type=self.content_type(mime_type),
            options=params,
        )


def factory(_context, request):
    return ViaClientService(
        via_client=ViaClient(
            service_url=request.host_url,
            html_service_url=request.registry.settings["via_html_url"],
            secret=request.registry.settings["via_secret"],
        )
    )
