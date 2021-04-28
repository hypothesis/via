"""A thin wrapper around ViaClient to make it a service."""
from h_vialib import ViaClient


class ViaClientService:
    """A wrapper service for h_vialib.ViaClient."""

    def __init__(self, via_client):
        self.via_client = via_client

    @staticmethod
    def is_pdf(mime_type):
        """Return True if the given MIME type is a PDF one."""
        return mime_type in ("application/x-pdf", "application/pdf")

    def url_for(self, url, mime_type, params):
        """Return a Via URL for the given `url`."""
        return self.via_client.url_for(
            url,
            content_type="pdf" if self.is_pdf(mime_type) else "html",
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
