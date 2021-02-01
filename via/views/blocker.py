"""View decorators to integrate with checkmate's API."""
import logging

from checkmatelib import CheckmateClient, CheckmateException
from pyramid.httpexceptions import HTTPTemporaryRedirect

logger = logging.getLogger(__name__)


def checkmate_block(view, url_param="url", allow_all=True):
    """Intended to be used as a decorator for pyramid views.

    The view must accept a url a query param.

    :param url_param name of the query param that contains the URL to check
    :allow_all Check against checkmate's allow list (True) or not.
    """

    def view_wrapper(context, request):
        checkmate = CheckmateClient(request.registry.settings["checkmate_url"])

        url = request.params[url_param]
        blocked = None
        try:
            blocked = checkmate.check_url(url, allow_all=allow_all)
        except CheckmateException:
            logging.exception("Failed to check url against checkmate")

        if blocked:
            return HTTPTemporaryRedirect(location=blocked.presentation_url)

        return view(context, request)

    return view_wrapper
