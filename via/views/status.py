import logging

from checkmatelib import CheckmateClient, CheckmateException
from pyramid.view import view_config

logger = logging.getLogger(__name__)


@view_config(route_name="status", renderer="json")
def status(request):
    settings = request.registry.settings

    checkmate = CheckmateClient(
        settings["checkmate_url"], settings["checkmate_api_key"]
    )

    status_ = "okay"

    try:
        checkmate.check_url("https://example.com/")
    except CheckmateException:
        status_ = "checkmate_failure"
        logger.exception("Checkmate request failed")

    return {"status": status_}
