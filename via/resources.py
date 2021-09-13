"""Context objects for views."""
from h_vialib import Configuration
from pyramid.httpexceptions import HTTPBadRequest


class URLResource:
    """Methods for routes which accept a 'url'."""

    def __init__(self, request):
        self._request = request

    def url_from_query(self):
        """Get the 'url' parameter from the query.

        :return: The URL as a string
        :raise HTTPBadRequest: If the url is missing or empty
        """
        try:
            url = self._request.params["url"].strip()
        except KeyError as err:
            raise HTTPBadRequest("Required parameter 'url' missing") from err

        if not url:
            raise HTTPBadRequest("Required parameter 'url' is blank")

        return self._normalise_url(url)

    def url_from_path(self):
        """Get the 'url' parameter from the path.

        :return: The URL as a string
        :raise HTTPBadRequest: If the url is missing or empty
        """

        url = self._request.path_qs[1:].strip()
        if not url:
            raise HTTPBadRequest("Required path part 'url` is missing")

        return self._normalise_url(url)

    @classmethod
    def _normalise_url(cls, url):
        """Return a normalized URL from user input.

        Take a URL from user input (eg. a URL input field or path parameter) and
        convert it to a normalized form.
        """
        if not (url.startswith("http://") or url.startswith("https://")):
            url = "https://" + url

        return Configuration.strip_from_url(url)
