"""A thin wrapper around ViaClient to make it a service."""
from h_vialib import ViaClient


class ViaClientService(ViaClient):
    """Place holder for a service, in case we want to diverge."""


def factory(_context, request):
    """Create a ViaClientService object from the request."""

    settings = request.registry.settings

    return ViaClientService(
        # Where we are coming from
        host_url=request.host_url,
        # Where we are going for general / HTML specifically
        service_url=request.host_url,
        html_service_url=settings["via_html_url"],
        # Secret used to sign everything
        secret=settings["via_secret"],
    )
