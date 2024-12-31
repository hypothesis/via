from checkmatelib import CheckmateException
from pyramid import view
from sentry_sdk import capture_message

from via.services import CheckmateService


@view.view_config(route_name="status", renderer="json", http_cache=0)
def status(request):
    body: dict[str, str | list] = {"status": "okay"}

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

    if "sentry" in request.params:
        capture_message("Test message from Via's status view")

    return body
