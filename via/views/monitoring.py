"""Monitoring views."""

from pyramid import response, view


@view.view_config(route_name="get_status")
def get_status(_request):
    """Status endpoint."""
    return response.Response(status_int=200, status="200 OK", content_type="text/plain")
