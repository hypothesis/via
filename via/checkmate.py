from checkmatelib import CheckmateClient


def checkmate(request):
    """Return the CheckmateClient object."""
    return CheckmateClient(
        request.registry.settings["checkmate_url"],
        request.registry.settings["checkmate_api_key"],
    )
