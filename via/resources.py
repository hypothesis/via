"""Context objects for views."""
from pyramid.httpexceptions import HTTPBadRequest

# pylint: disable=too-few-public-methods


class URLResource:
    """Methods for routes which accept a 'url'."""

    def __init__(self, request):
        self._request = request

    def url(self):
        """Get the 'url' parameter.

        :return: The URL as a string
        :raise HTTPBadRequest: If the url is missing or empty
        """
        try:
            url = self._request.params["url"]
        except KeyError as err:
            raise HTTPBadRequest("Required parameter 'url' missing") from err

        if not url:
            raise HTTPBadRequest("Required parameter 'url' is blank")

        return url
