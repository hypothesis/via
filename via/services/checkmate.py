from checkmatelib import BadURL as CheckmateBadURL
from checkmatelib import CheckmateClient, CheckmateException
from pyramid.httpexceptions import HTTPTemporaryRedirect

from via.exceptions import BadURL


class CheckmateService:
    def __init__(self, checkmate_client, allow_all, blocked_for, ignore_reasons):
        self._checkmate_client = checkmate_client
        self._allow_all = allow_all
        self._blocked_for = blocked_for
        self._ignore_reasons = ignore_reasons

    def check_url(self, url):
        return self._checkmate_client.check_url(
            url,
            allow_all=self._allow_all,
            blocked_for=self._blocked_for,
            ignore_reasons=self._ignore_reasons,
        )

    def raise_if_blocked(self, url):
        """Raise a redirect to Checkmate if the URL is blocked.

        This will sensibly apply all ignore reasons and other configuration for
        Checkmate.

        :param url: The URL to check
        :raises HTTPTemporaryRedirect: If the URL is blocked
        :raises BadURL: For malformed or private URLs
        """
        try:
            blocked = self.check_url(url)
        except CheckmateBadURL as exc:
            raise BadURL(exc, url=url) from exc
        except CheckmateException:
            blocked = None

        if blocked:
            raise HTTPTemporaryRedirect(location=blocked.presentation_url)


def factory(_context, request):
    return CheckmateService(
        checkmate_client=CheckmateClient(
            host=request.registry.settings["checkmate_url"],
            api_key=request.registry.settings["checkmate_api_key"],
        ),
        allow_all=request.registry.settings["checkmate_allow_all"],
        blocked_for=request.params.get("via.blocked_for"),
        ignore_reasons=request.registry.settings["checkmate_ignore_reasons"],
    )
