from checkmatelib import CheckmateClient, CheckmateException
from pyramid.httpexceptions import HTTPTemporaryRedirect


class ViaCheckmateClient(CheckmateClient):
    def __init__(self, request):
        super().__init__(
            host=request.registry.settings["checkmate_url"],
            api_key=request.registry.settings["checkmate_api_key"],
        )
        self._request = request

    def raise_if_blocked(self, url):
        """Raise a redirect to Checkmate if the URL is blocked.

        This will sensibly apply all ignore reasons and other configuration for
        Checkmate.

        :param url: The URL to check
        :raise HTTPTemporaryRedirect: If the URL is blocked
        """
        try:
            blocked = self.check_url(
                url,
                allow_all=self._request.registry.settings["checkmate_allow_all"],
                blocked_for=self._request.params.get("via.blocked_for"),
                ignore_reasons=self._request.registry.settings[
                    "checkmate_ignore_reasons"
                ],
            )

        except CheckmateException:
            blocked = None

        if blocked:
            raise HTTPTemporaryRedirect(location=blocked.presentation_url)
