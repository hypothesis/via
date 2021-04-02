"""Monitoring views."""

from pyramid import view


@view.view_config(route_name="get_status", renderer="json", http_cache=0)
def get_status(_request):
    """Status endpoint."""
    return {"status": "okay"}
