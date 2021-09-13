"""Context objects for views."""
from urllib.parse import urlparse

from h_vialib import Configuration
from pyramid.httpexceptions import HTTPBadRequest

from via.exceptions import BadURL


class URLResource:
    """Methods for routes which accept a 'url'."""

    def __init__(self, request):
        self._request = request

    def url_from_query(self):
        """Get the 'url' parameter from the query.

        :return: The URL as a string
        :raise HTTPBadRequest: If the URL is missing or empty
        :raise BadURL: If the URL is malformed
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
        :raise HTTPBadRequest: If the URL is missing or empty
        :raise BadURL: If the URL is malformed
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

        try:
            parsed = urlparse(url)
        except ValueError as exc:
            raise BadURL(url) from exc

        if not parsed.scheme:
            if not parsed.netloc:
                # Without a scheme urlparse often assumes the domain is the
                # path. To prevent this add a fake scheme and try again
                return cls._normalise_url("https://" + url)

            url = parsed._replace(scheme="https").geturl()

        return Configuration.strip_from_url(url)
