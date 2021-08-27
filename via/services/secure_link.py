from h_vialib.exceptions import TokenException
from h_vialib.secure import ViaSecureURL
from pyramid.httpexceptions import HTTPUnauthorized


def has_secure_url_token(view):
    """Require the request to have a valid signature."""

    def view_wrapper(context, request):
        if not request.find_service(SecureLinkService).request_is_valid(request):
            return HTTPUnauthorized()

        return view(context, request)

    return view_wrapper


class SecureLinkService:
    def __init__(self, secret, signed_urls_required):
        self._via_secure_url = ViaSecureURL(secret)
        self._signed_urls_required = signed_urls_required

    def request_is_valid(self, request):
        if not self._signed_urls_required:
            return True

        try:
            self._via_secure_url.verify(request.url)
        except TokenException:
            return False

        return True


def factory(_context, request):
    return SecureLinkService(
        secret=request.registry.settings["via_secret"],
        signed_urls_required=request.registry.settings["signed_urls_required"],
    )
