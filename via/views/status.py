"""Monitoring views."""

from checkmatelib import CheckmateException
from pyramid import view

from via.services import CheckmateService


@view.view_config(route_name="get_status", renderer="json", http_cache=0)
def get_status(request):
    """Status endpoint."""

    body = {"status": "okay"}

    if "include-checkmate" in request.params:
        checkmate_service = request.find_service(CheckmateService)

        try:
            checkmate_service.check_url("https://example.com/")
        except CheckmateException:
            body["down"] = ["checkmate"]
        else:
            body["okay"] = ["checkmate"]

    # If any of the components checked above were down then report the
    # status check as a whole as being down.
    if body.get("down"):
        request.response.status_int = 500
        body["status"] = "down"

    return body
