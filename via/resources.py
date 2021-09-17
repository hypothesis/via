"""Context objects for views."""
from urllib.parse import urlparse

from h_vialib import Configuration
from pyramid.httpexceptions import HTTPBadRequest

from via.exceptions import BadURL


class _URLResource:
    """Methods for routes which accept a 'url'."""

    def __init__(self, request):
        self._request = request

    @classmethod
    def _normalise_url(cls, url):
        """Return a normalized URL from user input.

        Take a URL from user input (eg. a URL input field or path parameter) and
        convert it to a normalized form.
        """

        try:
            parsed = urlparse(url)
        except ValueError as exc:
            raise BadURL(str(exc), url=url) from exc

        if not parsed.scheme:
            if not parsed.netloc:
                # Without a scheme urlparse often assumes the domain is the
                # path. To prevent this add a fake scheme and try again
                return cls._normalise_url("https://" + url.lstrip("."))

            url = parsed._replace(scheme="https").geturl()

        return Configuration.strip_from_url(url)


class PathURLResource(_URLResource):
    """Resource for routes expecting urls from the path."""

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


class QueryURLResource(_URLResource):
    """Resource for routes expecting urls from the query."""

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


def get_original_url(context):
    """Get the original URL from a provided context object (if any)."""

    if isinstance(context, QueryURLResource):
        getter = context.url_from_query
    elif isinstance(context, PathURLResource):
        getter = context.url_from_path
    else:
        return None

    try:
        return getter()
    except BadURL as err:
        return err.url
    except HTTPBadRequest:
        return None
