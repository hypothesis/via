"""View decorators to integrate with checkmate's API."""
import logging

from checkmatelib import CheckmateClient, CheckmateException
from h_vialib.exceptions import TokenException
from h_vialib.secure.url import ViaSecureURL
from pyramid.httpexceptions import HTTPTemporaryRedirect, HTTPUnauthorized

logger = logging.getLogger(__name__)


def checkmate_block(view, url_param="url", allow_all=True):
    """Intended to be used as a decorator for pyramid views.

    The view must accept a url a query param.

    :param url_param name of the query param that contains the URL to check
    :allow_all Check against checkmate's allow list (True) or not.
    """

    def view_wrapper(context, request):
        if not request.registry.settings["checkmate_enabled"]:
            return view(context, request)

        checkmate = CheckmateClient(
            request.registry.settings["checkmate_url"],
            request.registry.settings["checkmate_api_key"],
        )

        url = request.params[url_param]
        blocked_for = request.params.get("via.blocked_for")
        blocked = None
        try:
            blocked = checkmate.check_url(
                url,
                allow_all=allow_all,
                blocked_for=blocked_for,
                ignore_reasons=request.registry.settings["checkmate_ignore_reasons"],
            )
        except CheckmateException:
            logging.exception("Failed to check url against checkmate")

        if blocked:
            return HTTPTemporaryRedirect(location=blocked.presentation_url)

        return view(context, request)

    return view_wrapper


def has_secure_url_token(view, signature_param="via.sec"):
    """Require the request to have a valid signature in the "via.sec" query param."""

    def view_wrapper(context, request):
        signature = request.params.get(signature_param)
        if not signature and not request.registry.settings["signed_urls_required"]:
            return view(context, request)

        secure_token = ViaSecureURL(request.registry.settings["via_secret"])
        try:
            secure_token.verify(request.url)
        except TokenException:
            return HTTPUnauthorized()

        return view(context, request)

    return view_wrapper
