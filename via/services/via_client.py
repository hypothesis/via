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

    @staticmethod
    def is_video(mime_type):
        """Return True if the given MIME type is a PDF one."""
        return mime_type == "video/youtube"

    def url_for(self, url, mime_type, params):
        """Return a Via URL for the given `url`."""

        # TODO we use regular mimetypes over get_url_details and just switch to strings here for content_type.
        # I reckon we could include an Enum on ViaClient and use that everywhere instead
        content_type = "html"
        if self.is_pdf(mime_type):
            content_type = "pdf"
        elif self.is_video(mime_type):
            content_type = "video"

        return self.via_client.url_for(url, content_type, options=params)


def factory(_context, request):
    return ViaClientService(
        via_client=ViaClient(
            service_url=request.host_url,
            html_service_url=request.registry.settings["via_html_url"],
            secret=request.registry.settings["via_secret"],
        )
    )
