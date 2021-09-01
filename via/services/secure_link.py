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
    """A service for signing and checking URLs have been signed."""

    def __init__(self, secret, signed_urls_required):
        """Initialise the service.

        :param secret: Shared secret to sign and verify URLs with
        :param signed_urls_required: Enable or disable URL signing
        """
        self._via_secure_url = ViaSecureURL(secret)
        self._signed_urls_required = signed_urls_required

    def request_is_valid(self, request) -> bool:
        """Check whether a request has been signed.

        This will also pass if signing is disabled.
        """
        if not self._signed_urls_required:
            return True

        try:
            self._via_secure_url.verify(request.url)
        except TokenException:
            return False

        return True

    def sign_url(self, url):
        """Get a signed URL (if URL signing is enabled)."""

        if self._signed_urls_required:
            return self._via_secure_url.create(url)

        return url


def factory(_context, request):
    return SecureLinkService(
        secret=request.registry.settings["via_secret"],
        signed_urls_required=request.registry.settings["signed_urls_required"],
    )
