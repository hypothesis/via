"""View decorators to integrate with checkmate's API."""
from h_vialib.exceptions import TokenException
from h_vialib.secure.url import ViaSecureURL
from pyramid.httpexceptions import HTTPUnauthorized


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
