from checkmatelib import CheckmateClient, CheckmateException
from pyramid.httpexceptions import HTTPTemporaryRedirect


def checkmate(request):
    """Return the CheckmateClient object."""
    return CheckmateClient(
        request.registry.settings["checkmate_url"],
        request.registry.settings["checkmate_api_key"],
    )


def raise_if_blocked(request, url):
    """Raise a redirect to Checkmate if the URL is blocked.

    This will sensibly apply all ignore reasons and other configuration for
    Checkmate.

    :param request: Pyramid request object
    :param url: The URL to check
    :raise HTTPTemporaryRedirect: If the URL is blocked
    """
    try:
        blocked = request.checkmate.check_url(
            url,
            allow_all=request.registry.settings["checkmate_allow_all"],
            blocked_for=request.params.get("via.blocked_for"),
            ignore_reasons=request.registry.settings["checkmate_ignore_reasons"],
        )

    except CheckmateException:
        blocked = None

    if blocked:
        raise HTTPTemporaryRedirect(location=blocked.presentation_url)
