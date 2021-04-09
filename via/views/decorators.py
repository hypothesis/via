"""View decorators to integrate with checkmate's API."""
from checkmatelib import CheckmateClient, CheckmateException
from h_vialib.exceptions import TokenException
from h_vialib.secure.url import ViaSecureURL
from pyramid.httpexceptions import HTTPTemporaryRedirect, HTTPUnauthorized


def checkmate_block(view):
    """Intended to be used as a decorator for pyramid views.

    The view must accept a url a query param.
    """

    def view_wrapper(context, request):
        checkmate = CheckmateClient(
            request.registry.settings["checkmate_url"],
            request.registry.settings["checkmate_api_key"],
        )

        try:
            blocked = checkmate.check_url(
                request.params["url"],
                allow_all=request.registry.settings["checkmate_allow_all"],
                blocked_for=request.params.get("via.blocked_for"),
                ignore_reasons=request.registry.settings["checkmate_ignore_reasons"],
            )
        except CheckmateException:
            blocked = None

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
