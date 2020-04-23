"""Context objects for views."""
from pyramid.httpexceptions import HTTPBadRequest

# pylint: disable=too-few-public-methods


class URLResource:
    """Methods for routes which accept a 'url'."""

    def __init__(self, request):
        self._request = request
        self._nginx_server = self._request.registry.settings["nginx_server"]

    def static_proxy_url_for(self, url):
        return f"{self._nginx_server}/proxy/static/{url}"

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
