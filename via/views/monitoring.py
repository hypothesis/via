"""Monitoring views."""

from pyramid import view


@view.view_config(route_name="get_status", renderer="json")
def get_status(_request):
    """Status endpoint."""
    return {"status": "okay"}
